"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10466 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps a verdict onto. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region — which the consumer spec view elides
— is changed, so ``markers.same_spec`` holds and the ``prove_correct``
obligation survives with a byte-identical header) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method, ``publishPositions entries``, computes
the published positions for a single message from its recorded entries. Each
entry carries a source name, a line index, and an opaque identity tag; the
observable is a ``List Pos`` of (source, line) pairs. Two independent
postcondition clauses pin the result:

  (Q1) out = orderedPositions entries
       — the DISTINCT (source, line) pairs among the entries, in ascending
       order. This fixes the whole result at once: which positions survive
       (identity tags dropped, coincident positions collapsed) AND their order.
  (Q2) out.Nodup
       — the result carries no repeated position.

``entries`` is the sole FREE input; both clauses must hold for every value it
takes, which is what makes the partial-domain rivals below refutable at a
concrete point.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini because
    a read-only input carries a fractional heap permission an impl can overwrite
    (the sibling's ``frame-mutation-canonical`` / ``frame-mutation-insert-sorted``
    cases write to a half-permission ``recorded`` / ``xs``). Lean and Velvet are
    referentially transparent: ``entries`` is an immutable value (no ``mut``
    binder on any input in this bundle), there is no heap and no aliasing, so
    there is no read-only input to mutate and no substitute probe to build. Not
    fabricated (per the porting map: this class is vacuous on Lean/Velvet).
  * UNGROUNDED-ORACLE ECHO — N/A as a WRONG echo. Both clauses are grounded
    entirely in the argument ``entries``: ``orderedPositions`` is spelled out as
    a projection + deduplication + total-order sort over the input, and the
    ``axioms`` region is empty (no opaque answer key to echo). An impl that
    "echoes the oracle" (returns ``orderedPositions entries``) is simply the
    CORRECT impl. The honest substitutes are the structurally-different positive
    controls, not a wrong echo.
  * PARTIAL-DOMAIN / VALUE — APPLIES. A rival can be correct on the all-distinct
    sub-domain (a list whose projected positions are already distinct and
    ascending) yet diverge once a position recurs or the input is truncated:
    never deduplicating (the pre-fix behaviour), deduplicating a proper prefix
    only, or omitting the deduplication step while keeping the sort. Each attacks
    a clause and is refuted where it diverges.

CARRIER NOTE — the sort is NOT independently F2P-load-bearing here. The failing
test records positions whose insertion order already coincides with the
ascending order, so a faithful real patch that deduplicated WITHOUT reordering
(the reporter's own first attempt, ``list(set(...))`` / an insertion-order
dedup) still produces exactly the asserted list and WOULD resolve the F2P. A
"dedup-but-don't-sort" impl is therefore a legitimately CORRECT refinement on
the F2P domain, not a break — so it is not shipped as a uniqueness rival (a
verify-does-not-imply-resolve claim would be false for it). The reject rivals
below all attack behaviour whose faithful real counterpart genuinely fails the
F2P (see each ``refinement``). See the module footer for the nagini accounting.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, so a witness reaches the
postcondition through Velvet's own tester machinery (``extract_program_for`` …
``derive_tester_for``): ``publishPositionsTester args = false`` says the
extracted program's result violates the postcondition at that concrete input.
Every witness here is stated over a COMPUTABLE PROJECTION of the postcondition,
never over the whole conjunction, and that is forced by the carrier rather than
chosen for convenience. The projection ``toPos`` and the deduplication ``.dedup``
DO reduce over literal entries, but the ``mergeSort`` in clause (Q1) is
well-founded recursion the kernel will not unfold, so a ``decide`` aimed at the
undivided tester gets STUCK — ``did not reduce to `isTrue` or `isFalse` `` — for
EVERY claim, true or false. A build that fails that way discriminates nothing:
the same error appears for a true claim about the same impl, so its exit code
would attest to a refutation that was never performed. (This was measured on this
bundle, not assumed: the naive ``simp [NonDetT.run, publishPositions]; decide``
shape does elaborate against the sort-free rivals and does fail on gold, and is
still worthless, because gold's failure is the stuck instance
``(....dedup.mergeSort posLe).hasDecEq`` and not a decision.)

So each witness peels the conjunction with ``rintro`` and keeps exactly one
conjunct, chosen so the surviving goal avoids the sort:

  * the (Q2) witnesses keep the Nodup conjunct and transport it across the sort
    by the sort's PERMUTATION invariant (``List.mergeSort_perm _ posLe``, whose
    ``.nodup_iff`` says a permutation preserves Nodup), leaving
    ``(List.map toPos <lit>).dedup.Nodup`` — reducible;
  * the (Q1) witness keeps the equality conjunct and takes ``congrArg
    List.length``, then rewrites by the sort's LENGTH invariant
    (``List.length_mergeSort``), leaving an arithmetic clash between two
    literal lengths — reducible.

Neither uses the sort's VALUE; each uses only an invariant of it. Confirmed on
both sides for all three: the rival's build closes, and the frozen build fails
with ``decide`` *proving the proposition false* (e.g. ``... .dedup.Nodup → False
is false``, ``True → False is false``) — a real decision, so the discrimination
is genuine. No ``witness_reference`` is needed or used: the frozen impl is
loop-free, and what blocked reduction was the spec's own sort, which a reference
impl of the SAME spec could not avoid either. No ``sorry`` / ``admit`` /
``native_decide`` is used, and no witness binds a hypothesis (so there are no
assumptions that could be jointly unsatisfiable).

BINDER / CLAUSE COVERAGE. The one spec binder is ``entries``; the four reject
witnesses vary its content across four DISTINCT input points (a length-2 list
with a coincident position at (['a'],1); a length-2 list with a coincident
position at (['b'],2); a length-2 list of two DISTINCT positions in ascending
order; a length-2 list of two distinct positions in DESCENDING order), so no
rival's divergence is confined to a single probed input.

Clause (Q2) Nodup is attacked by the two duplicate-carrying inputs (the impl
emits a repeated position). Clause (Q1) is attacked along BOTH of the facets it
independently pins:

  * WHICH positions / how many — the drop-last rival (a length mismatch against
    the sorted distinct set);
  * their ORDER — the descending rival, which publishes exactly the right
    positions with the right multiplicity in the wrong sequence.

That last one is why the descending rival is not redundant, and the reason it is
shipped: it is a PERMUTATION of the correct answer OF THE CORRECT LENGTH, so both
invariants the other witnesses lean on (Nodup-across-a-permutation, length) are
blind to it by construction. Without it the ordering half of (Q1) would be
asserted by the spec and probed by nothing — and the ordering half is precisely
the facet this bundle's leakage disposition records as gold-only, i.e. the one a
reader has most reason to want evidence for. Note also that the descending input
is the only NON-ASCENDING point in the battery: at every ascending input this
rival agrees with gold exactly, so no other witness's input could have exposed
it, and a battery probing only ascending inputs would say nothing about the sort.

AXIOM lane: the ``axioms`` region is empty (no consumed axiom). The set-based
deduplication and the total-order sort are A-REFERENCE deep models validated
against the real standard-library primitives by G-AX / axiom_check.py, NOT this
gate's job. ``AXIOM_TESTS`` is dropped.

AUDIT STATUS. Independently re-derived post-port with real builds. The four
reject witnesses reproduced exactly and each additionally cleared the forgery
test (flip the claim; reveal the hypothesis type; rebuild at an agreement point)
— see the footer for the observed exit codes. Two POSITIVE-lane defects were
found and repaired: the admissibility case was the frozen file verbatim (a
restatement of G-VERIFY, replaced by a positive that discharges both clauses at
a concrete F2P-shaped input), and both soundness positives were definitionally
equal let-reshapes (a non-def-equal ``foldr`` reshape was added, which the frozen
proof body does not close). No hole was found in the frozen spec: eight new
wrong impls were all rejected. The divergence class is REJECTED BY THE SPEC and
recorded as a limit of the WITNESS machinery, with the measured error, not as a
spec hole and not as a vacuous class.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10466"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the method's editable
# ---- `-- impl-start` / `-- impl-end` block and is unique in the file (both
# ---- facts asserted at load by _swap). Every variant replaces this two-line
# ---- impl body; the frozen spec, the method header, and the `prove_correct`
# ---- obligation are untouched, so `same_spec` holds by construction.
_IMPL = (
    "    let result := ((entries.map toPos).dedup).mergeSort posLe\n"
    "    return result\n"
)

# ---- proof-region anchor. The frozen `prove_correct` tactic body, verbatim and
# ---- unique in the file. `variant_scope` admits a changed TACTIC body (the
# ---- `prove_correct publishPositions` header must survive, and does — measured:
# ---- variant_problems == [] for every case below), which is what lets a positive
# ---- ADD a `have` before replaying the frozen script. Cases that re-tune the
# ---- proof re-emit the header byte-for-byte and append `_PROOF.split(...)[1]`,
# ---- so the frozen script cannot drift out from under them.
_PROOF = (
    "prove_correct publishPositions by\n"
    "  loom_solve\n"
    "  · exact (List.mergeSort_perm ((entries.map toPos).dedup) posLe).nodup_iff.mpr\n"
    "      (List.nodup_dedup _)\n"
    "  · rfl\n"
)
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


# ---------------------------------------------------------------------------
# Witness builders. A witness reaches the postcondition through the tester
# machinery, checked in a file whose `prove_correct` block has been stripped, so
# no tactic script can mask the verdict. The Nodup-attacking witnesses unfold
# the tester and `decide` on the fully-reduced result (projection + dedup are
# reducible); the length-attacking witness refutes clause (Q1) via a length
# invariant of the sort, since `mergeSort` itself is irreducible under `decide`.
# ---------------------------------------------------------------------------

def _witness_nodup(entries_lit):
    """Refute clause (Q2) at `entries_lit` (a term with a coincident projected
    position): the impl emits a repeated position, so the tester is `false`.

    Stated over a COMPUTABLE PROJECTION of the postcondition rather than over
    the whole conjunction. Reducing the (Q1) conjunct would force the kernel
    through the well-founded `mergeSort` in `orderedPositions`, which it cannot
    unfold: `decide` on the full tester gets STUCK (`did not reduce to isTrue or
    isFalse`) rather than deciding, and a build that failed by stuck reduction
    discriminates nothing — the identical error appears for a TRUE claim, so the
    exit code would attest to a refutation never performed. So the witness peels
    the conjunction with `rintro`, keeps only the Nodup conjunct, and transports
    it across the sort via its PERMUTATION invariant
    (`List.mergeSort_perm ... |>.nodup_iff`) instead of computing the sort. What
    remains — `(List.map toPos <lit>).dedup.Nodup` — is a projection + a
    deduplication over literals, which reduces, so both sides genuinely DECIDE:
    the rival's build closes and the frozen build fails with `decide` *proving
    the proposition false*, not with a stuck instance.

    The `first | rw ... | skip` serves both rival shapes with one script: a rival
    that skips the sort has no `mergeSort` to transport across, one that keeps it
    does. Neither branch can close the goal on its own — the `decide` does.
    """
    return (
        "extract_program_for publishPositions\n"
        "prove_precondition_decidable_for publishPositions\n"
        "prove_postcondition_decidable_for publishPositions\n"
        "derive_tester_for publishPositions\n\n"
        "example : publishPositionsTester " + entries_lit + " = false := by\n"
        "  unfold publishPositionsTester publishPositionsExec\n"
        "  simp only [NonDetT.run, publishPositions, decide_true, if_true]\n"
        "  rw [decide_eq_false_iff_not]\n"
        "  rintro ⟨hnd, -⟩\n"
        "  first\n"
        "    | rw [(List.mergeSort_perm _ posLe).nodup_iff] at hnd\n"
        "    | skip\n"
        "  revert hnd\n"
        "  decide\n"
    )


def _witness_length(entries_lit):
    """Refute clause (Q1) at `entries_lit` via `List.length_mergeSort`: the
    sorted distinct set of ALL entries has a length the truncated impl cannot
    match.

    Same computable-projection discipline as `_witness_nodup`, on the other
    conjunct: `rintro` keeps the equality, `congrArg List.length` weakens it to a
    length equation, and `List.length_mergeSort` discharges the sort's
    contribution WITHOUT reducing the sort (which is well-founded-recursive and
    would leave `decide` stuck). What remains is a clash between two literal
    lengths, which decides on both sides.
    """
    return (
        "extract_program_for publishPositions\n"
        "prove_precondition_decidable_for publishPositions\n"
        "prove_postcondition_decidable_for publishPositions\n"
        "derive_tester_for publishPositions\n\n"
        "example : publishPositionsTester " + entries_lit + " = false := by\n"
        "  unfold publishPositionsTester publishPositionsExec\n"
        "  simp only [NonDetT.run, publishPositions, decide_true, if_true]\n"
        "  rw [decide_eq_false_iff_not]\n"
        "  rintro ⟨-, hq⟩\n"
        "  have hlen := congrArg List.length hq\n"
        "  simp only [orderedPositions, List.length_mergeSort] at hlen\n"
        "  revert hlen\n"
        "  decide\n"
    )


def _witness_order(entries_lit):
    """Refute clause (Q1)'s ORDER content at `entries_lit`: the rival emits the
    right SET of positions, with the right multiplicity, in the wrong sequence.

    The length and permutation invariants used by the two witnesses above are
    both blind to this rival — it is a permutation of the correct answer and has
    the correct length — so this witness must reach the sort's actual VALUE. It
    can, but not via `decide`: the `Decidable` instance gets stuck on
    `mergeSort`'s well-founded recursion (`rfl` fails on a two-element literal
    sort for the same reason). Handing the sort's own equations to `simp`
    (`List.mergeSort`, plus `posLe` / `lcharLt` so the comparator's branches
    resolve) DOES compute it on a literal, which is the documented
    "unfold the operation for `simp`" route around a stuck `decide`.

    `simp ... at hq` then closes the goal by reducing the rival's hypothesis to
    `False`. On the frozen impl the same reduction turns `hq` into `True`,
    leaving `⊢ False` unsolved — a real reduction on both sides (no stuck
    instance), so the discrimination is genuine.
    """
    return (
        "extract_program_for publishPositions\n"
        "prove_precondition_decidable_for publishPositions\n"
        "prove_postcondition_decidable_for publishPositions\n"
        "derive_tester_for publishPositions\n\n"
        "example : publishPositionsTester " + entries_lit + " = false := by\n"
        "  unfold publishPositionsTester publishPositionsExec\n"
        "  simp only [NonDetT.run, publishPositions, decide_true, if_true]\n"
        "  rw [decide_eq_false_iff_not]\n"
        "  rintro ⟨-, hq⟩\n"
        "  simp [orderedPositions, toPos, List.mergeSort, posLe, lcharLt] at hq\n"
    )


# Distinct probed inputs (pts=4). `_DUP_A` / `_DUP_B` each carry a coincident
# projected position (same source+line, differing identity tag) at DIFFERENT
# points; `_DISTINCT` carries two genuinely distinct positions ALREADY in
# ascending order; `_UNSORTED` carries two distinct positions in DESCENDING
# order, the only input point at which the ordering clause has any content
# (at every ascending input a sort-free impl agrees with gold).
_DUP_A = "[(['a'], (1:Int), ['u']), (['a'], (1:Int), ['v'])]"
_DUP_B = "[(['b'], (2:Int), ['u']), (['b'], (2:Int), ['v'])]"
_DISTINCT = "[(['a'], (1:Int), ['u']), (['b'], (2:Int), ['v'])]"
_UNSORTED = "[(['b'], (1:Int), ['u']), (['a'], (2:Int), ['v'])]"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. Each reshapes only how the pipeline value is
    # bound (introducing named intermediate locals) without changing the data
    # flow, so the emitted list is `orderedPositions entries` on every input
    # and the frozen `prove_correct` body still discharges. If a faithful
    # correct reshape could not verify, the spec would be SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-let-split-pipeline",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL,
            "    let ps := entries.map toPos\n"
            "    let uniq := ps.dedup\n"
            "    let result := uniq.mergeSort posLe\n"
            "    return result\n"),
        "rationale": "a correct reshape that binds the projection and the "
                     "deduplication to named locals before sorting computes the "
                     "same list, so clauses (Q1) `out = orderedPositions "
                     "entries` and (Q2) `out.Nodup` both still discharge; must "
                     "verify (else SPEC-TOO-STRONG). The value flow is identical, "
                     "so the frozen proof body closes unchanged.",
    },
    {
        "id": "pos-bind-projection",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL,
            "    let ps := entries.map toPos\n"
            "    let result := ps.dedup.mergeSort posLe\n"
            "    return result\n"),
        "rationale": "hoisting only the per-entry projection into a typed local "
                     "leaves the deduplicated, sorted result unchanged, so both "
                     "clauses still hold; a correct reshape must verify. A second "
                     "structurally-distinct positive on the single obligation. "
                     "NOTE (audit): like pos-let-split-pipeline this is a "
                     "DEFINITIONALLY EQUAL let-reshape — measured, in that the "
                     "unchanged frozen `rfl` leg still closes it. That makes it "
                     "an honest but weak SPEC-TOO-STRONG control; "
                     "pos-foldr-projection below is the one that is not def-equal.",
    },
    {
        "id": "pos-foldr-projection",
        "kind": "soundness",
        "expect": "verify",
        # A correct reshape that is NOT definitionally equal to the frozen impl:
        # the per-entry projection is built by an explicit `foldr` instead of
        # `List.map`. Same list on every input, but the frozen `rfl` leg does NOT
        # close it (measured: exit 1 with the frozen proof body), so the case
        # must supply the bridging induction. That is what makes it a real
        # SPEC-TOO-STRONG probe rather than a restatement: it asks whether the
        # spec accepts a faithful correct impl whose SHAPE the frozen proof was
        # not tuned to, which the two let-reshapes above cannot ask.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    let ps := entries.foldr (fun e acc => toPos e :: acc) []\n"
                  "    let result := ps.dedup.mergeSort posLe\n"
                  "    return result\n"),
            _PROOF,
            "prove_correct publishPositions by\n"
            "  have hfm : ∀ (l : List Entry),\n"
            "      l.foldr (fun e acc => toPos e :: acc) [] = l.map toPos := by\n"
            "    intro l; induction l with\n"
            "    | nil => rfl\n"
            "    | cons a t ih => simp [ih]\n"
            "  loom_solve\n"
            "  · simp only [hfm]\n"
            "    exact (List.mergeSort_perm ((entries.map toPos).dedup) posLe).nodup_iff.mpr\n"
            "      (List.nodup_dedup _)\n"
            "  · simp only [hfm, orderedPositions]\n"),
        "rationale": "a CORRECT reshape that is not definitionally equal to the "
                     "frozen impl: it builds the per-entry projection with an "
                     "explicit `foldr` rather than `List.map`, then deduplicates "
                     "and sorts as before. The emitted list is "
                     "`orderedPositions entries` on every input, so clauses (Q1) "
                     "and (Q2) both still hold and it MUST verify (else "
                     "SPEC-TOO-STRONG). Unlike the two let-reshapes above, the "
                     "frozen `rfl` leg does NOT close this one — measured: with "
                     "the frozen proof body verbatim the file fails (exit 1) on "
                     "the Nodup leg's type mismatch — so the case carries the "
                     "bridging `foldr = map` induction and reproves the same two "
                     "obligations. That is precisely why it belongs here: it is "
                     "the only positive in this battery testing that the spec "
                     "admits a faithful impl the frozen proof was not tuned to. "
                     "No new declaration and no assumption: the induction is a "
                     "`have` inside the existing tactic body and the "
                     "`prove_correct publishPositions` header is byte-identical.",
    },

    # =====================================================================
    # ADMISSIBILITY. The method declares no `require`, so the literal "a normal
    # input satisfies the precondition" probe has no content — nothing could
    # exclude an input. The analogue on a TOTAL carrier is the obligation being
    # unsatisfiable at exactly an F2P-shaped input, and what tests that is a
    # positive that DISCHARGES the obligation at that concrete input, by
    # evaluation, as a `have`, before closing the frozen obligation verbatim.
    #
    # The earlier port shipped `module = _BASE` here — the frozen file byte for
    # byte. That passes honestly and attests to nothing this bundle did not
    # already record: it is the same build G-VERIFY and G-GOLD already run, so
    # its `verified` restated those gates rather than probing the spec. Replaced
    # (see the AUDIT note in the footer) with the shape that carries content.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        # Two `have`s discharged BY EVALUATION at one F2P-shaped input — a
        # message that records the SAME position twice (differing only in its
        # identity tag), a second position on the same source, and a position on
        # a different source. Then `clear` them, so the frozen obligation still
        # closes on its own terms and the case cannot pass BECAUSE of the have.
        # The `prove_correct publishPositions` header is re-emitted byte-for-byte
        # and the frozen tactic script is appended by construction.
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct publishPositions by\n"
            "  have hAdmissQ1 : orderedPositions "
            "[(['f'], (1:Int), ['u']), (['f'], (1:Int), ['v']), "
            "(['f'], (2:Int), ['w']), (['y'], (1:Int), ['z'])]\n"
            "      = [(['f'], (1:Int)), (['f'], (2:Int)), (['y'], (1:Int))] := by\n"
            "    simp [orderedPositions, toPos, List.mergeSort, posLe, lcharLt]\n"
            "  have hAdmissQ2 : (orderedPositions "
            "[(['f'], (1:Int), ['u']), (['f'], (1:Int), ['v']), "
            "(['f'], (2:Int), ['w']), (['y'], (1:Int), ['z'])]).Nodup := by\n"
            "    rw [hAdmissQ1]; decide\n"
            "  clear hAdmissQ1 hAdmissQ2\n" + _PROOF.split("\n", 1)[1]),
        "rationale": "PRECOND-TOO-STRONG probe, aimed at what that analogue IS "
                     "on a total carrier: the obligation must be SATISFIABLE — "
                     "and non-degenerately so — at an F2P-shaped input. The two "
                     "`have`s discharge both clauses by EVALUATION at one "
                     "concrete message that records a position TWICE (same "
                     "source and line, differing identity tag), plus a second "
                     "line on that source and a position on another source: "
                     "(Q1) `orderedPositions` there is exactly the three "
                     "distinct positions in ascending order, and (Q2) that list "
                     "is Nodup. If the postcondition admitted no value at such "
                     "an input — the shape the fix targets — the first `have` "
                     "could not be discharged. The `have`s are then `clear`ed "
                     "and the frozen script replayed verbatim, so the case "
                     "cannot pass because of them. Measured live: as written it "
                     "verifies (exit 0), and each of three WRONG literals for "
                     "the same input fails (exit 1) — duplicate kept, order "
                     "reversed, last position dropped — so the `have` is live "
                     "and not a restatement of the frozen build.",
    },

    # =====================================================================
    # UNIQUENESS / PARTIAL-DOMAIN rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input, and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-no-dedup",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behaviour: publish the raw per-entry projection in
        # insertion order, with NO collapsing of coincident positions. Correct on
        # the all-distinct sub-domain, wrong the moment a position recurs.
        "module": _swap(
            _BASE, _IMPL,
            "    let result := entries.map toPos\n"
            "    return result\n"),
        "refinement": "emitting the raw projection with no deduplication is "
                      "exactly the pre-fix behaviour: coincident positions "
                      "(entries that share a source and line, differing only in "
                      "their identity tag) are all published, so the location "
                      "list carries repeats. The failing test records the same "
                      "position several times for one message and asserts the "
                      "published list is deduplicated; this rival publishes the "
                      "duplicates, so it would NOT resolve — this is precisely "
                      "the change the spec senses.",
        "rationale": "REJECT from clause (Q2) `out.Nodup` (and (Q1)): the raw "
                     "projection of a message with a coincident position is not "
                     "Nodup and is not the distinct ordered set. PARTIAL-DOMAIN: "
                     "correct only where every projected position is already "
                     "distinct. Refuted at a length-2 list whose two entries "
                     "project to the same position (['a'],1).",
        "witness": _witness_nodup(_DUP_A),
    },
    {
        "id": "weak-sort-no-dedup",
        "kind": "uniqueness",
        "expect": "reject",
        # Sorts the projected positions but SKIPS the deduplication: coincident
        # positions are kept and merely reordered. Right order, wrong multiplicity.
        "module": _swap(
            _BASE, _IMPL,
            "    let result := (entries.map toPos).mergeSort posLe\n"
            "    return result\n"),
        "refinement": "sorting without collapsing coincident positions is what a "
                      "counterpart that reached for an order-only fix (`sorted(...)` "
                      "without the set) would do: it orders the locations but "
                      "still lists each recorded occurrence, so a message with a "
                      "repeated position emits it twice. The failing test asserts "
                      "each distinct location appears ONCE; a sorted-with-repeats "
                      "list fails that assertion. It would NOT resolve.",
        "rationale": "REJECT from clause (Q2) `out.Nodup`: sorting preserves "
                     "multiplicity, so the coincident position survives twice and "
                     "the result is not Nodup, while (Q1) demands the distinct "
                     "ordered set. NEAR-MISS on order — refuted at a DIFFERENT "
                     "duplicate point (['b'],2) than weak-no-dedup, so the binder "
                     "is genuinely varied.",
        "witness": _witness_nodup(_DUP_B),
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Deduplicates and sorts a proper PREFIX of the entries, silently dropping
        # the last recorded entry. Correct on the sub-domain where the last
        # entry's position already occurs earlier, wrong otherwise.
        "module": _swap(
            _BASE, _IMPL,
            "    let result := ((entries.dropLast.map toPos).dedup).mergeSort posLe\n"
            "    return result\n"),
        "refinement": "deduplicating and sorting a proper prefix (dropping the "
                      "last recorded entry) is what an off-by-one bound on the "
                      "traversal would produce. On a message whose final recorded "
                      "position occurs nowhere earlier it loses that location "
                      "entirely, so the published list is missing a location the "
                      "failing test asserts is present. It would NOT resolve.",
        "rationale": "REJECT from clause (Q1) `out = orderedPositions entries`: "
                     "the postcondition is over ALL entries, but the rival "
                     "publishes the distinct ordered set of a prefix. On a list "
                     "of two DISTINCT positions the results differ in LENGTH "
                     "(one vs two), which the witness derives via "
                     "List.length_mergeSort. Refuted at a length-2 list of two "
                     "distinct positions — the third distinct input point, and "
                     "the only one attacking (Q1) structurally rather than (Q2).",
        "witness": _witness_length(_DISTINCT),
    },
    {
        "id": "weak-descending-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Publishes the right SET of distinct positions, with the right
        # multiplicity, but in DESCENDING order. Correct on every input whose
        # distinct positions number 0 or 1 (where the two orders coincide);
        # wrong as soon as two distinct positions are published.
        "module": _swap(
            _BASE, _IMPL,
            "    let result := (((entries.map toPos).dedup).mergeSort posLe).reverse\n"
            "    return result\n"),
        "refinement": "reversing the published order is what a counterpart that "
                      "ordered the locations the wrong way round would do. The "
                      "failing test asserts an EXACT list of locations for a "
                      "message, not a set: it pins both which locations appear "
                      "and the sequence they appear in, and for the message it "
                      "checks that sequence has three distinct entries. A "
                      "descending publication yields those same three locations "
                      "in the opposite sequence, so the list comparison fails and "
                      "it would NOT resolve. Note this is a STRICTLY stronger "
                      "claim than the module header's non-ported "
                      "'dedup-but-do-not-sort' case: that impl coincides with the "
                      "asserted sequence on the failing test's own input (whose "
                      "insertion order is already ascending) and so would "
                      "resolve, which is exactly why it is NOT shipped as a "
                      "rival; a REVERSED order diverges from it on that same "
                      "input, so this rival's non-resolution is real.",
        "rationale": "REJECT from the ORDER content of clause (Q1) "
                     "`out = orderedPositions entries` — the one facet no other "
                     "rival here attacks. The two invariants the other witnesses "
                     "lean on are both BLIND to this rival: it is a permutation "
                     "of the correct answer (so the Nodup/permutation route "
                     "cannot see it) and has the correct length (so the "
                     "length route cannot either). The witness therefore reduces "
                     "the sort's actual VALUE, which `simp` can do on a literal "
                     "even though `decide` gets stuck on it. PARTIAL-DOMAIN: "
                     "correct wherever fewer than two distinct positions are "
                     "published. Refuted at the fourth distinct input point, and "
                     "the only DESCENDING one — at every ascending input this "
                     "rival agrees with gold, so no other witness's input could "
                     "have exposed it.",
        "witness": _witness_order(_UNSORTED),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation rivals, 3 uniqueness rivals) plus 1
# axiom-lane entry. This bundle models the SAME single behaviour (publish the
# distinct, ascending positions of a message) but as ONE deep-modeled method
# rather than nagini's canonical_positions + insert_sorted split, so the frame
# and helper-specific cases collapse.
#
#   sibling case                     -> here                        disposition
#   ---------------------------------------------------------------------------
#   pos-control-merge-equal-branches -> pos-let-split-pipeline       PORTED
#   (none)                           -> pos-bind-projection          ADDED (2nd positive)
#   (none)                           -> pos-foldr-projection         ADDED (audit; not def-equal)
#   admissibility-gold-impl          -> admiss-f2p-shaped-input      PORTED (audit: re-aimed)
#   frame-mutation-canonical         -> (none)                       VACUOUS
#   frame-mutation-insert-sorted     -> (none)                       VACUOUS
#   partial-domain-no-dedup-no-sort  -> weak-no-dedup                PORTED
#   partial-domain-keep-duplicate-key-> weak-sort-no-dedup           PORTED (re-expressed)
#   partial-domain-drop-last         -> weak-drop-last               PORTED
#   (none)                           -> weak-descending-order        ADDED (order facet)
#   axref-dedup-sort-sound           -> (none)                       DROPPED (G-AX lane)
#
# VACUOUS (frame-mutation, x2): the sibling rejects impls that WRITE to a
#   read-only half-permission input (`recorded`, `xs`). This backend is
#   referentially transparent and this bundle declares no `mut` binder on any
#   input, so there is no read-only input to overwrite and no substitute probe.
#   Not fabricated (per the porting map: this class is vacuous on Lean/Velvet).
# PORTED (weak-sort-no-dedup): the sibling's keep-duplicate-key rival attacks the
#   insert-step's dedup-on-equal. This bundle has no separate insertion step; the
#   equivalent WRONG behaviour on the whole operation is "sort but do not
#   deduplicate", which keeps a coincident position — the same failure the
#   sibling case targets (a repeated location in the output), re-expressed
#   against the single deep-modeled method.
# DROPPED (axiom lane): the sibling's AXIOM_TESTS validates the deep model's
#   dedup/sort against the real `sorted(set(...))`. That is G-AX / axiom_check.py's
#   job; this gate ignores AXIOM_TESTS. Nothing to probe here.
#
# NOT PORTED as a rival — the SORT clause is not independently F2P-load-bearing.
#   A "dedup-but-do-not-sort" impl would be a WRONG echo of nagini's sort, but on
#   this instance the F2P records positions whose insertion-dedup order already
#   equals the ascending order, so a faithful real patch that deduplicated
#   without reordering (the reporter's own `list(set(...))` attempt) STILL
#   resolves the F2P. Shipping it as a uniqueness rival would assert a false
#   verify-does-not-imply-resolve claim, so it is deliberately omitted. The four
#   rivals shipped all attack behaviour whose faithful real counterpart genuinely
#   fails the F2P.
#
#   ADDED (weak-descending-order) is the ordering attack that IS legitimate, and
#   it exists because of the omission above rather than in spite of it. Not
#   sorting is unobservable on the F2P input (its insertion order is already
#   ascending); publishing in REVERSE is not, since the F2P asserts an exact
#   list of three locations for one message and a reversed list of the same
#   three fails that comparison. So the ordering clause DOES carry a genuine
#   verify-does-not-imply-resolve rival — just not the sort-free one — and
#   leaving the facet unattacked would have been the thinner battery, not the
#   more honest one.
#
# BINDER / CLAUSE COVERAGE. The sole spec binder is `entries`. The four reject
#   witnesses vary it across four DISTINCT input points (a duplicate at
#   (['a'],1); a duplicate at (['b'],2); two distinct ASCENDING positions; two
#   distinct DESCENDING positions), none shared, so `entries` is genuinely
#   discriminated (pts=4). Both independent clauses are attacked, and (Q1) along
#   both facets it pins:
#     (Q2) `out.Nodup`                    weak-no-dedup, weak-sort-no-dedup
#                                         (each at a different coincident position)
#     (Q1) which/how many positions       weak-drop-last (length mismatch, via
#                                         List.length_mergeSort)
#     (Q1) the ORDER of those positions   weak-descending-order (a permutation of
#                                         the correct answer, of the correct
#                                         length — invisible to both invariants
#                                         above, hence its own witness at the
#                                         battery's only descending input)
#
# WITNESS DISCRIMINATION. Each witness elaborates against its rival and FAILS
#   against the frozen solution, so every rejection is attributed to the spec,
#   not to a tactic gap. Verified during authoring with real builds: rival exit
#   0, gold exit 1, for all four.
#
#   AND — the part that matters on this carrier — gold's failure is a DECISION,
#   not a stuck reduction. The frozen spec's `mergeSort` is well-founded
#   recursion the kernel will not unfold, so a `decide` aimed at the undivided
#   postcondition is stuck for every claim regardless of truth, and such a build
#   proves nothing: the identical error appears for a TRUE claim about the same
#   impl, so a forged witness asserting the rival is CORRECT would clear both
#   halves. An earlier revision of this battery shipped exactly that shape for
#   the two (Q2) rivals and was correctly refused. The shipped witnesses instead
#   state each refutation over a computable PROJECTION (a Nodup conjunct
#   transported across the sort by its permutation invariant; a length conjunct
#   by its length invariant), so the surviving goal never contains the sort.
#   Observed gold-side errors, quoted from the builds:
#     weak-no-dedup         `... .dedup.Nodup → False` is false
#     weak-sort-no-dedup    `... .dedup.Nodup → False` is false
#     weak-drop-last        `True → False` is false
#     weak-descending-order `hq : True ⊢ False` unsolved
#   The first three are `decide` PROVING a proposition false; the fourth is the
#   same thing via `simp`, which reduced the sort's value on both sides and left
#   gold's hypothesis as `True` (nothing to contradict) while closing the rival's.
#   In every case the kernel actually EVALUATED the claim, so no exit code here
#   stands in for a refutation that never happened.
#
#   The ordering witness needed a different tactic for the same reason it needed
#   to exist: it is the one claim that cannot be settled by an invariant of the
#   sort and must reach the sort's VALUE. `decide` cannot (its instance sticks on
#   the well-founded recursion — `rfl` fails on a literal two-element sort), but
#   handing `simp` the sort's own equations plus the comparator's does compute it.
#
#   No `witness_reference` is used, and none would help: the frozen impl is
#   loop-free (nothing here elaborates through `Classical.choice`), and the term
#   that blocked reduction is the SPEC's own sort, which any reference impl of
#   the same spec must also mention. The repair had to be a computable
#   projection, which is the first of the two documented routes.
#
# ---------------------------------------------------------------------------
# AUDIT (independent, post-port). Every case was re-derived with real builds.
# The four reject witnesses reproduced exactly (rival exit 0 / gold exit 1, gold
# signatures byte-identical to the recorded ones), and each was additionally put
# through the FORGERY test rather than judged by reading its error:
#
#   * Flip the claim. The same tester equation asserted `= true` — i.e. that the
#     impl is CORRECT at the witness's own input — was built on both sides. On
#     GOLD it VERIFIES (exit 0) at both the duplicate point and the descending
#     point; on every rival it FAILS (exit 1, `unsolved goals ... ⊢ False`). So
#     gold's exit code tracks the claim in both directions: the witnesses are not
#     resting on a tactic mismatch.
#   * Reveal the type. Replacing the final step with a deliberate type error
#     prints the hypothesis's real type. For the ORDER witness, gold gives
#     `hq has type True` (simp PROVED the equation for gold) while the rival gives
#     the concrete unsatisfied equation `(....mergeSort posLe).reverse = ....
#     mergeSort posLe`. For the LENGTH witness, gold gives `hlen has type True`
#     and the rival the concrete length clash. That pair is a genuine refutation.
#   * Agreement points. Each witness rebuilt at an input where its rival AGREES
#     with gold fails against the rival too (exit 1), so no witness is a script
#     that closes regardless of the input it names.
#
# Two defects were found in the POSITIVE lane and fixed; both were hollow-pass
# shapes, not wrong claims.
#
# 1. admiss-gold-impl was `module = _BASE` — the frozen file byte for byte. Its
#    `verified` was the same build G-VERIFY and G-GOLD already record, so it
#    attested to no property of the spec. Corpus-wide this is the minority shape
#    (37 of 480 velvet admissibility cases) and a sibling cell documents having
#    been audited off it for exactly this reason. Replaced by
#    admiss-f2p-shaped-input, which discharges BOTH clauses by evaluation at one
#    F2P-shaped input (a position recorded twice, a second line on that source, a
#    position on another source) as `have`s, `clear`s them, then closes the frozen
#    obligation verbatim. Measured: verifies (exit 0); and with a WRONG literal
#    for that same input it fails (exit 1) in all three directions tried
#    (duplicate kept, order reversed, last position dropped), so the `have` is
#    load-bearing rather than decorative.
#
# 2. Both soundness positives were DEFINITIONALLY EQUAL let-reshapes: measured,
#    in that the unchanged frozen `rfl` leg still closes both. A def-equal
#    reshape cannot fail unless the spec is broken outright, so neither probed
#    whether the spec admits a correct impl the frozen PROOF was not tuned to.
#    Added pos-foldr-projection, which builds the projection by `foldr` instead
#    of `List.map`: gold-equal on every input, but the frozen proof body does NOT
#    close it (measured exit 1), so it carries a `foldr = map` induction and
#    reproves the same two obligations. Verifies (exit 0).
#
# SPEC probes, all negative — no hole found. Eight NEW wrong impls the battery
# did not contain were built against the frozen spec and ALL were rejected
# (exit 1): a line-only comparator, a source-only comparator, drop-FIRST entry,
# truncate-to-8, project the identity tag instead of the line, return `[]`
# always, append a sentinel position, and dedup-twice-without-sorting. Clause
# (Q1) is an exact functional equation pinning the whole result, so SPEC-TOO-WEAK
# has very little surface here. Four correct reshapes were also tried: an inlined
# projection lambda and an eta-expanded comparator verify under the frozen proof;
# the `foldr` reshape verifies once reproven (now shipped); and sort-THEN-dedup is
# gold-equal but its reproof needs a dedup/mergeSort commutation lemma that was
# not closed within budget — recorded as UNCERTAIN, NOT as a spec hole, since the
# ensures clauses accept the identical value and the obstacle is a tuned-proof
# mismatch.
#
# DIVERGENCE LANE (F′) - CLOSED BY THE SEMANTICS, and unshippable for a witness
# reason rather than a spec one. This bundle sets
# `loom.semantics.termination "total"` (line 4) and opens `TotalCorrectness`
# (line 7), so a diverging rival IS rejected on the termination obligation, in
# BOTH the shapes it can take, measured rather than assumed:
#   * NO measure: a `while` with no `decreasing` annotation makes the MODULE fail
#     at the linter (`Decreasing annotations are required in total correctness
#     semantics`), and that same error fires in the WITNESS file too: it broke
#     even a trivial `example : (1:Nat) + 1 = 2 := by decide` appended to that
#     module (exit 1 on the half that must SUCCEED). So such a rival can only ever
#     land as `witness-unproven`, an inconclusive outcome, never a pass.
#   * WITH a measure that does not decrease, the shape that cannot be dismissed as
#     merely missing the annotation: `while 0 < 1` carrying `done_with 1 < 0` and
#     `decreasing (0 : Nat)` elaborates, and is then REJECTED at exit 1 on the
#     MEASURE's own descent goal,
#         unsolved goals
#         case «decreasing_1: (0 : Nat)» ... |- 0 < 0
#     so it is not laundered through the unreachable exit either. Its witness
#     still cannot attribute the rejection: the tester rewrite fails against the
#     un-normalised `forIn Lean.Loop.mk` term, the documented stuck-unification
#     shape the gate screens for.
# Mechanism, so neither bullet rests on one build: `set_option
# loom.semantics.termination "total"` itself opens the `TotalCorrectness` scope
# (Loom, `MonadAlgebras/WP/Options.lean`, the `openScope `TotalCorrectness` arm),
# line 7 opens it again, and `TotalCorrectness.WPGen.forWithInvariantLoop` takes
# the `measure` and emits `measure b' < measure b` as a goal the proof must
# discharge; only the `PartialCorrectness` twin takes a measure and discards it.
# So this is a limit of the WITNESS machinery on this carrier, not a vacuous class
# and not a spec hole: the rejection is real in both shapes, but no witness can
# attribute it, so the case is unshippable under the witness rule rather than
# unnecessary. No spec hole is escalated from this class.
AXIOM_TESTS = []
