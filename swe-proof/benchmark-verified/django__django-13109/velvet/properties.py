"""properties.py — G-PBT falsification battery for django__django-13109 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct validateExists`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a record-collection carrier):

  validateExists (rows : List Record) (target : Int) return (out : Bool)
    ensures out = existsMatch target rows          -- the sole, load-bearing clause

The method decides whether the consulted record collection contains a record
whose referenced field matches the target identity. The pure region pins the
whole outcome as a total function of the method's own two inputs:

  existsMatch target []        = false
  existsMatch target (r :: rs) = matchesTarget target r || existsMatch target rs
  matchesTarget target r       = (r.key == target)     -- INDEPENDENT of r.hidden

The decisive property this spec encodes is that ``existsMatch`` consults EVERY
record — a record whose key matches contributes ``true`` regardless of whether it
is filtered out of the model's everyday/default view (``Record.hidden``). A check
that consults only the everyday-view subset (drops the hidden records) therefore
DISAGREES with the post-image exactly on a matching-but-hidden record — which is
the behaviour the F2P tests exercise (an archived target validates through the
complete-view manager but not the everyday one).

INPUT BINDERS of the sole predicate, and how each is exercised:
  * ``rows`` — the consulted record collection. Its LENGTH (0/1/2), each
    record's ``key``, and each record's ``hidden`` flag all feed the decision.
    The reject witnesses vary length, key, and hidden across their points.
  * ``target`` — the identity searched for; drives which record (if any) matches.
    Varied across witness points.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS here. The nagini sibling holds BOTH
    collection inputs at a fractional heap permission (``Acc(list_pred(.),1/2)``)
    and rejects two rivals that WRITE BACK into a read-only input for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: every parameter is
    an immutable value, this method declares no ``mut`` binder, there is no heap
    and no aliasing. There is no read-only input to overwrite and no permission
    system to trip, so the class is vacuous. No substitute is fabricated.
  * IGNORE-CHOICE (nagini ``weak-ignore-choice``) — NO COUNTERPART here. The
    nagini spec conjoins an opaque ``choice_permitted`` (the field's
    ``limit_choices_to`` narrowing) as the SECOND conjunct of ``reference_holds``
    and rejects a rival that drops it. On this carrier the ``limit_choices_to``
    narrowing is upstream/downstream of the modeled existence test and is applied
    IDENTICALLY by both collection sources (mapping.md §2, §3), so it is not part
    of the modeled discriminator — there is no ``choice_permitted`` clause in this
    spec to attack. Legitimately omitted as carrier narrowing (see the footer).
  * UNGROUNDED-ORACLE ECHO — N/A, as the sibling records. The post-image is
    ``existsMatch target rows``, a concrete ``def`` in the ``pure`` region
    computing the outcome from the method's own arguments; the ``axioms`` region
    is empty, so there is no opaque answer key to echo. The honest positive
    controls are the cheapest faithful reshapes (the ``pos-*`` cases).
  * TERMINATION / DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a
    diverging rival is REJECTED rather than admitted. This bundle sets
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
  * PARTIAL-DOMAIN / VALUE — heavily exercised. ``weak-prepatch`` is right on
    every non-hidden record but wrong on a matching HIDDEN record (the F2P bug);
    ``weak-skip-head`` is right except on a record the traversal skips; the two
    baselines pin the decision in both directions.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is a backward ``while`` loop;
its EXTRACTED program does not reduce under ``decide`` (the loop stays symbolic),
so the reject rivals are written STRAIGHT-LINE (``return <expr>`` over the pure
``List`` primitives) — the shape is free, the spec view is untouched, and the
extracted straight-line program reduces fully. Each reject rival carries a
machine-checked refutation ``witness``, checked in a file whose ``prove_correct``
block has been stripped so no tactic script can mask the verdict. The ``Bool``
return carrier already has ``DecidableEq``, so no ``deriving`` / ``axiom`` /
``sorry`` / ``native_decide`` is involved.

THE ASYMMETRY, STATED HONESTLY (an earlier revision of this file got this wrong,
and correcting it is why each witness below now has THREE legs). The frozen
program's extracted form ``validateExistsExec`` is a ``while`` loop whose
fixpoint does NOT kernel-reduce, so ``decide`` on its tester gets stuck for EVERY
input — measured, including at inputs where the frozen program is RIGHT. All of
these fail against the frozen solution with ``did not reduce to isTrue or
isFalse``:

  * ``validateExistsTester [{key := 7, hidden := true}] 7 = false``  (exit 1)
  * ``validateExistsTester [{key := 7, hidden := true}] 7 = true``   (exit 1) —
    a TRUE claim about the frozen program, and it still fails;
  * ``validateExistsTester [] 0 = validateExistsTester [] 0``        (exit 1) —
    a pure TAUTOLOGY, and it still fails.

So for a rival reshaped into a loop-free closed form, a bare ``Tester = false``
witness satisfies the gate's gold-side leg by NON-REDUCTION rather than by
refutation, and attests nothing on its own. Measured directly: the tautology
above passes BOTH gate halves (elaborates against the loop-free ``return true``
rival, exit 0; fails on the frozen solution, exit 1). Independently confirmed
that a bare ``Tester = false`` does not separate WRONG from merely LOOP-FREE:
each of the four witnesses was rebuilt against a CORRECT loop-free impl
(``return existsMatch target rows``) and every one ELABORATED there (exit 0) —
i.e. the bare form was passing for the rivals' shape, not their wrongness.

WHAT CLOSES IT. Each reject witness states its refutation in three
machine-checked legs, so its force does not rest on the gold-side stall:

  (a) ``validateExistsExec <input> = DivM.res <concrete wrong value>`` by
      ``rfl`` — pins the value the rival's extracted program actually returns,
      which also rules out the tester's ``| _ => false`` arm as the source of
      ``Tester = false``;
  (b) ``(<concrete wrong value> : Bool) ≠ existsMatch <target> <rows>`` by
      ``decide`` — that value is wrong per the SPEC'S OWN post-image at that
      input, decided on ground data with no reference to any impl;
  (c) the ``Tester = false`` claim the gate's protocol consumes.

(a)+(b) together are a self-contained counterexample: the rival returns X, and
the spec's post-image at that input is not X. Cross-checked out-of-band with
``scripts/lean_verify.sh`` (recorded, not gate-visible): every three-leg witness
below ELABORATES against its rival (exit 0), FAILS against the frozen solution
(exit 1), and — the check the gate structurally cannot run — FAILS against BOTH
correct reshapes, ``pos-return-fold`` and ``pos-commute-disjunct`` (exit 1 each),
leg (a) reporting ``rfl failed: not definitionally equal``. That is what shows
these rivals are refuted for being WRONG rather than for being loop-free.

WHICH SUBJECT THE GATE ACTUALLY USES, AND WHY THAT IS THE STRONG CASE. An audit
pass re-derived all three legs for every reject case and found something the
docstring above did not state: because gold's ``while`` fixpoint is stuck, the
gate's own stuck-reduction screen fires on the frozen solution and it FALLS BACK
to a verifying positive of this same spec as the witness's second subject
(``meta.json`` records ``witness_subject: "a verifying positive from this battery
(gold cannot decide)"``). That fallback is what makes these rejections real
rather than hollow, and it is measured, not assumed:

  * against the frozen solution, leg (c) fails with ``decide ... did not reduce to
    `isTrue` or `isFalse` `` — a STALL, carrying no information about the claim;
  * against ``pos-return-fold`` (the loop-free positive the gate selects), leg (c)
    fails with ``decide PROVED that the proposition ... is false`` — a DECIDED
    refutation of the claim, on an impl the gate independently re-verifies first.

The forgery test (attack B′) confirms the exit code tracks the CLAIM on that
subject and not merely the shape. Flipping leg (a) to assert the CORRECT value at
the same input reverses every exit code: it BUILDS against ``pos-return-fold``
(exit 0) and FAILS against each rival (exit 1, ``rfl failed`` naming the flipped
value). Flipping leg (c) to ``Tester = true`` likewise builds on the positive
(exit 0) and fails on the rival. Against the frozen solution, by contrast, the
flipped claim fails with the byte-identical stall — which is exactly why leg (c)
alone would have been hollow, and why legs (a)+(b) and the fallback subject
carry the attestation. Measured controls: a pure TAUTOLOGY
(``Tester [] 0 = Tester [] 0``) fails on the frozen solution (exit 1) but BUILDS
on ``pos-return-fold`` (exit 0), so the fallback subject is not satisfied by
vacuous claims; and a bare one-leg ``Tester = false`` witness, rebuilt for all
five original points, is REFUTED on ``pos-return-fold`` (exit 1, decided) as well
as elaborating on its rival — so on the subject the gate actually uses, even the
bare form discriminates. The three-leg form is kept regardless: legs (a)+(b) are
readable as a counterexample without reference to which subject was chosen.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no deep-model
reference (the collection-source primitive is modeled DEEPLY as ``existsMatch``);
this gate ignores ``AXIOM_TESTS`` regardless.

OUT-OF-BAND PROBES run during the audit of this battery (recorded, not shipped as
cases — each was a full variant built with ``scripts/lean_verify.sh``):

  * SPEC-TOO-WEAK probe — seven NEW wrong impls beyond the rivals below, aimed at
    what they left unattacked: ``|| r.hidden`` (over-accept on `hidden`),
    ``rows.length > 0`` (ignore the key entirely), ``take (length - 1)`` (skip the
    LAST record rather than the head), ``rows.all`` for ``rows.any``,
    ``rows.contains {key := target, hidden := false}`` (structural equality, so it
    demands hidden=false), head-only inspection, and ``r.key == target + 1``
    (off-by-one on the key). ALL SEVEN were rejected (exit 1) — no spec hole. The
    first of them was strong enough to keep, and ships below as
    ``weak-hidden-accepts``.
    A SECOND audit pass added seven more, aimed at the binder sub-domains the
    shipped witnesses never reach: the match COUNT (``== 1``; and the parity fold
    ``xor``), the SIGN of the key (``r.key.natAbs == target.natAbs``), ordering
    for equality (``target ≤ r.key``), a collection-wide veto on any hidden
    record, last-record-only inspection, and dropping the LAST record
    (``take (length - 1)``). Each was tried under FIVE admissible proof scripts
    (the frozen one plus four retunings, so a rejection cannot be blamed on the
    tactic script alone) — 35 builds, ALL rejected (exit 1). No spec hole. Two of
    them probed genuinely unattacked sub-domains and were strong enough to keep;
    they ship below as ``weak-count-exactly-one`` (existence vs uniqueness) and
    ``weak-magnitude-key`` (signed equality vs equality of magnitudes).
  * SPEC-TOO-STRONG probe — NEW correct reshapes with retuned proofs.
    ``return (rows.map (fun r => r.key)).contains target`` VERIFIES (exit 0), and
    ``return rows.any (fun r => target == r.key)`` — the equality written in the
    other direction — VERIFIES (exit 0). So the spec admits faithful reshapes off
    both the loop-vs-fold and the projection axes, not just the two positives
    below. A SECOND audit pass re-ran this lane wider and closed the one reshape
    the first pass had left open: a FORWARD loop accumulating over ``rows.take j``
    (invariant ``found = existsMatch target (rows.take j)``, ``done_with j =
    rows.length``) now VERIFIES (exit 0). Its residual step goal is discharged
    inside the elided tactic body by two ``have``s — append-distribution for
    ``existsMatch`` over ``++`` by induction, then ``rw
    [List.take_succ_eq_append_getElem hk]`` — so the earlier "not closed within
    the build budget" note was an authoring gap, not a property of the spec, and
    is withdrawn. The spec therefore admits reshapes off the loop DIRECTION axis
    too. Four further correct reshapes verify on the same footing (``! rows.all
    (fun r => ! matchesTarget target r)``, ``rows.foldr``,
    ``decide (0 < (rows.filter ...).length)``, and the two-sided-``≤`` spelling of
    the equality), each needing only equality-bridging lemmas
    (``eq_comm``/``grind``) and no change to the spec.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no deep-model
reference (the collection-source primitive is modeled DEEPLY as ``existsMatch``);
this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13109"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN (and including)
# the method's `-- impl-start` / `-- impl-end` marker lines. Every rival and
# reshape edits ONLY this block (and, for reshapes/admissibility, the elided
# `prove_correct` tactic body), so the spec view is untouched and same_spec
# holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    let mut found : Bool := false\n"
    "    let mut i := rows.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ rows.length\n"
    "      invariant found = existsMatch target (rows.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let r := rows[i - 1]!\n"
    "      found := matchesTarget target r || found\n"
    "      i := i - 1\n"
    "    return found\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = (
    "prove_correct validateExists by\n"
    "  loom_solve\n"
    "  rw [existsMatch_drop_step rows target i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `validateExistsTester <rows> <target> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict. There are no `require` clauses, so
# ---- every input reaches the postcondition. `Record` is a two-field structure
# ---- with `DecidableEq`, the return carrier is `Bool`; `decide` settles each
# ---- statement with no derived instance needed. ----
_TESTER = (
    "extract_program_for validateExists\n"
    "prove_precondition_decidable_for validateExists\n"
    "prove_postcondition_decidable_for validateExists\n"
    "derive_tester_for validateExists\n\n"
)


def _witness(rows, target, got):
    """A THREE-LEG refutation at one concrete input.

    `rows` / `target` are the input; `got` is the Bool the rival's extracted
    program actually returns there (necessarily the negation of the spec's
    post-image, since that is what makes this a counterexample).

    Leg (c) alone would be hollow on this bundle: gold's `while` fixpoint does
    not kernel-reduce, so `decide` on ANY tester claim — including a tautology —
    fails against the frozen solution, and the gate's gold-side leg would be
    satisfied by that stall rather than by refutation (see the module docstring).
    Legs (a)+(b) carry the actual counterexample and are what separate a WRONG
    rival from a merely LOOP-FREE one: they fail against the correct loop-free
    reshapes too, with `rfl failed: not definitionally equal`.
    """
    args = f"{rows} {target}"
    return (
        _TESTER
        # (a) the value the rival's extracted program really returns.
        + f"example : validateExistsExec {args} = DivM.res {got} := by\n  rfl\n\n"
        # (b) that value is wrong per the SPEC'S OWN post-image at that input —
        #     ground data, no reference to any impl.
        + f"example : ({got} : Bool) ≠ existsMatch {target} {rows} := by\n"
        + "  decide\n\n"
        # (c) the `Tester = false` claim the gate's protocol consumes.
        + f"example : validateExistsTester {args} = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-return-fold",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the loop entirely and return the pure fold directly.
        # Same value on every input (`out = existsMatch target rows`), a
        # radically different executable shape (no mutable state, no loop). The
        # reproof collapses to `loom_solve` (no loop VC remains).
        "module": _impl_reproved(
            "    return existsMatch target rows",
            "prove_correct validateExists by\n  loom_solve"),
        "rationale": "structurally-different CORRECT impl: it discards the "
                     "backward loop and returns the pure existence fold "
                     "directly, so `out = existsMatch target rows` holds "
                     "definitionally. No loop VC remains, so the reproof is a "
                     "bare `loom_solve`. A faithful correct reshape must verify, "
                     "else SPEC-TOO-STRONG (a correct impl rejected for a "
                     "non-spec reason).",
    },
    {
        "id": "pos-commute-disjunct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the gold backward loop and every invariant verbatim, but
        # accumulate the running result with the disjuncts COMMUTED
        # (`found || matchesTarget ...` instead of `matchesTarget ... || found`).
        # `||` is commutative, so the loop still tracks membership over the
        # scanned suffix; the reproof adds `Bool.or_comm` to close the reshaped
        # step goal.
        "module": _impl_reproved(
            "    let mut found : Bool := false\n"
            "    let mut i := rows.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ rows.length\n"
            "      invariant found = existsMatch target (rows.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let r := rows[i - 1]!\n"
            "      found := found || matchesTarget target r\n"
            "      i := i - 1\n"
            "    return found",
            "prove_correct validateExists by\n"
            "  loom_solve\n"
            "  rw [existsMatch_drop_step rows target i (by omega) (by omega)]\n"
            "  simp_all [Bool.or_comm]"),
        "rationale": "structurally-different CORRECT impl: the gold backward loop "
                     "and all invariants are kept, but the running disjunction is "
                     "accumulated with the operands COMMUTED (`found || match` vs "
                     "`match || found`). `||` is commutative, so the loop still "
                     "tracks `existsMatch target (rows.drop i)` and "
                     "`out = existsMatch target rows` holds; the reproof adds "
                     "`Bool.or_comm` to the frozen step. Must verify, else "
                     "SPEC-TOO-STRONG on disjunct order.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here (every input is in-domain). The
    # residual admissibility risk on a total-domain spec is that the decision is
    # DEGENERATE at the interesting point — an existence fold that ignored the
    # hidden flag by COLLAPSING (always true, or always false) would read like a
    # live one. This case discharges an in-region assert pinning that the fold is
    # non-degenerate exactly where the F2P bug lives: a matching HIDDEN record
    # still yields true, an empty collection yields false, and a non-matching
    # record yields false. The rest of the impl is kept verbatim so the method's
    # own obligation still discharges; the proof is retuned to also close the
    # assert VC (`decide`), a body elided from the spec view. The assert is LIVE
    # (a false claim leaves an unsolved goal — verified during authoring).
    # =====================================================================
    {
        "id": "admiss-hidden-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (existsMatch 7 [{ key := 7, hidden := true }] = true ∧\n"
            "       existsMatch 7 ([] : List Record) = false ∧\n"
            "       existsMatch 7 [{ key := 3, hidden := false }] = false))\n"
            "    let mut found : Bool := false\n"
            "    let mut i := rows.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ rows.length\n"
            "      invariant found = existsMatch target (rows.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let r := rows[i - 1]!\n"
            "      found := matchesTarget target r || found\n"
            "      i := i - 1\n"
            "    return found",
            "prove_correct validateExists by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (rw [existsMatch_drop_step rows target i (by omega) (by omega)]; simp_all)\n"
            "    | decide"),
        "rationale": "the existence decision is satisfiable AND non-degenerate at "
                     "the F2P-shaped point: a matching record that is HIDDEN from "
                     "the everyday view still yields `true` (`existsMatch 7 "
                     "[{key:=7,hidden:=true}] = true`), an empty collection yields "
                     "`false`, and a non-matching record yields `false` — so the "
                     "fold neither collapses to a constant nor ignores the "
                     "matching-hidden case the fix hinges on. The in-region assert "
                     "must discharge (else the modeled behaviour would be "
                     "degenerate / the obligation vacuous); the impl is kept "
                     "verbatim so the ensures still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its extracted tester reduces
    # under `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-prepatch-everyday-view",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: consult only the everyday/default-VIEW subset — a
        # record contributes only when it matches AND is NOT hidden. Correct on
        # every non-hidden record, wrong on a matching HIDDEN record.
        "module": _impl(
            "    return rows.any (fun r => matchesTarget target r && ! r.hidden)"),
        "refinement": "this IS the pre-patch behaviour: the existence test ranges "
                      "over the everyday/default VIEW, which drops records the "
                      "model's default view filters out (e.g. an archived row). "
                      "Its faithful real counterpart is the unchanged repo, which "
                      "reports NO matching record for a target whose only stored "
                      "record is hidden by the default view — failing the F2P "
                      "tests that assert such a reference validates "
                      "(test_FK_validates_using_base_manager, "
                      "test_validate_foreign_key_to_model_with_overridden_manager). "
                      "It is the exact bug the fix removes (G-DIFF); it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = existsMatch target rows`: `existsMatch` "
                     "consults every record regardless of `hidden`, but the rival "
                     "masks matching-hidden records with `&& ! r.hidden`, so on a "
                     "collection whose only matching record is hidden the rival "
                     "returns `false` where the post-image demands `true`. "
                     "Refuted at a single matching HIDDEN record — the sub-domain "
                     "where the fix and the bug differ. It is the only rival that "
                     "SUPPRESSES a keyed match on `hidden` (`weak-hidden-accepts` "
                     "abuses the flag in the other direction), and the only one "
                     "whose wrongness needs `hidden = true` at all: at this point "
                     "`weak-skip-head` and `weak-never-exists` are wrong too (they "
                     "are wrong on any single matching record), so what isolates "
                     "THIS rival is not that it alone fails here but that it alone "
                     "fails ONLY here — it agrees with the post-image on every "
                     "non-hidden record, which is why `weak-hidden-accepts` and the "
                     "two baselines carry their own separating points.",
        "witness": _witness("[{ key := 7, hidden := true }]", "7", "false"),
    },
    {
        "id": "weak-skip-head",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN / off-by-one: skip the first record of the collection
        # (`rows.drop 1`) before testing membership. Correct for every target
        # whose matching record is not uniquely at the head, wrong when the only
        # matching record sits at index 0.
        "module": _impl(
            "    return (rows.drop 1).any (fun r => matchesTarget target r)"),
        "refinement": "an off-by-one real patch whose membership test skipped the "
                      "first record of the consulted collection would report no "
                      "match for a target whose only stored record sorts to the "
                      "head position — failing the accept-expecting validation on "
                      "that input class while passing on every other. A genuine "
                      "PARTIAL-DOMAIN break (the record inspected/skipped at the "
                      "boundary), not a blanket wrong impl; it would NOT resolve.",
        "rationale": "REJECT from `out = existsMatch target rows`: `existsMatch` "
                     "consults record 0, but the rival drops it (`rows.drop 1`), "
                     "so on a collection whose only matching record is at index 0 "
                     "the rival returns `false` where the post-image demands "
                     "`true`. Refuted at a two-record collection whose head "
                     "matches and whose tail does not — a distinct input from the "
                     "prepatch witness (both records here are non-hidden, so the "
                     "discrimination is the traversal, not the hidden flag).",
        "witness": _witness(
            "[{ key := 5, hidden := false }, { key := 0, hidden := false }]",
            "5", "false"),
    },
    {
        "id": "weak-always-exists",
        "kind": "uniqueness",
        "expect": "reject",
        # The cheapest "forgot to do the work" baseline that never rejects:
        # always report a match. Wrong on any collection with no matching record.
        "module": _impl("    return true"),
        "refinement": "always reporting a match is what a real patch that "
                      "short-circuited the existence test (or deleted it) would "
                      "do — it accepts a reference to a record that is NOT stored "
                      "at all (a dangling reference). It fails every "
                      "reject-expecting validation test (an absent target must be "
                      "rejected, e.g. test_wrong_FK_value_raises_error); it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = existsMatch target rows`: on a collection "
                     "with no matching record `existsMatch` is `false`, but the "
                     "rival returns `true`. Refuted at the EMPTY collection "
                     "(`rows = []`, `target = 0`) — a point where the skip-head "
                     "rival is CORRECT, so this rival carries its own separating "
                     "input; it also varies the `rows` binder to length 0.",
        "witness": _witness("([] : List Record)", "0", "true"),
    },
    {
        "id": "weak-never-exists",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual baseline that always rejects: never report a match. Wrong on
        # any collection that contains a matching record.
        "module": _impl("    return false"),
        "refinement": "never reporting a match is what a real patch that "
                      "hard-coded the existence test to empty (or compared "
                      "against the wrong, always-empty source) would do — it "
                      "rejects EVERY reference, including references to "
                      "genuinely-stored records. It fails every accept-expecting "
                      "validation test (a live target must validate, e.g. "
                      "test_correct_FK_value_validates); it would NOT resolve.",
        "rationale": "REJECT from `out = existsMatch target rows`: on a collection "
                     "that contains a matching record `existsMatch` is `true`, but "
                     "the rival returns `false`. Refuted at a single matching "
                     "NON-HIDDEN record (`[{key:=9,hidden:=false}]`, `target=9`) — "
                     "a point where the prepatch rival and `weak-hidden-accepts` "
                     "are both CORRECT (neither masks nor manufactures a match on a "
                     "non-hidden keyed record), so this point separates the "
                     "always-reject baseline from both `hidden` rivals. It does NOT "
                     "separate it from `weak-skip-head`, which is also wrong on a "
                     "single matching record; that separation is carried the other "
                     "way, by the empty-collection point where skip-head is right.",
        "witness": _witness("[{ key := 9, hidden := false }]", "9", "false"),
    },
    {
        "id": "weak-hidden-accepts",
        "kind": "uniqueness",
        "expect": "reject",
        # The OTHER direction of abusing `Record.hidden`, which no other rival
        # here attacks: instead of MASKING a matching hidden record, treat a
        # hidden record as a match regardless of its key. Correct on every
        # collection whose hidden records happen to match, wrong on a hidden
        # record whose key does NOT match.
        "module": _impl(
            "    return rows.any (fun r => matchesTarget target r || r.hidden)"),
        "refinement": "a real patch that reached the complete collection but let "
                      "a record's exclusion-from-the-everyday-view stand IN PLACE "
                      "OF the field comparison would validate a reference to an "
                      "identity that is NOT stored at all, whenever some unrelated "
                      "record is hidden — a dangling reference accepted. It fails "
                      "the reject-expecting validation tests (an absent target must "
                      "be rejected, e.g. test_wrong_FK_value_raises_error) on every "
                      "model whose everyday view filters anything, while passing the "
                      "accept-expecting ones; it would NOT resolve.",
        "rationale": "REJECT from `out = existsMatch target rows`: `matchesTarget` "
                     "is INDEPENDENT of `hidden` (it is `r.key == target` alone), so "
                     "on a collection whose only record is hidden with a "
                     "NON-matching key the post-image demands `false` while the "
                     "rival returns `true`. Refuted at `[{key:=3,hidden:=true}]` "
                     "with `target=7` — a point where `weak-prepatch-everyday-view` "
                     "is CORRECT (both agree there is no match on key), so this "
                     "rival carries its own separating input. Together with the "
                     "prepatch rival it pins `hidden` in BOTH directions: it may "
                     "neither suppress a keyed match nor manufacture one.",
        "witness": _witness("[{ key := 3, hidden := true }]", "7", "true"),
    },
    {
        "id": "weak-count-exactly-one",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Every shipped rival above is refuted at a point with AT
        # MOST ONE matching record, so nothing pinned that the decision is
        # EXISTENCE rather than UNIQUENESS. This rival counts the matches and
        # demands exactly one — indistinguishable from the post-image on every
        # collection with 0 or 1 matching record, wrong as soon as TWO records
        # match. It is a genuine near-miss, not a blanket wrong impl.
        "module": _impl(
            "    return (rows.filter (fun r => matchesTarget target r)).length == 1"),
        "refinement": "a real patch that asked the consulted collection for the "
                      "UNIQUE matching record rather than merely whether one "
                      "exists (a get-style lookup that treats more than one hit "
                      "as a failure) would reject a reference whose identity is "
                      "carried by two or more stored records — a duplicate that "
                      "the everyday view may well collapse to one while the "
                      "complete view surfaces both. It rejects a live, "
                      "genuinely-stored target on exactly that input class while "
                      "passing everywhere else, failing the accept-expecting "
                      "validation tests there; it would NOT resolve.",
        "rationale": "REJECT from `out = existsMatch target rows`: `existsMatch` is "
                     "an OR-fold, true as soon as ANY record matches and monotone "
                     "in further matches, but the rival is true only when the match "
                     "count is exactly 1, so on a collection with TWO matching "
                     "records it returns `false` where the post-image demands "
                     "`true`. Refuted at `[{key:=4,hidden:=false},{key:=4,"
                     "hidden:=true}]` with `target=4` — the first witness in this "
                     "battery with more than one matching record, a sub-domain "
                     "where EVERY other rival here is correct (prepatch sees the "
                     "non-hidden match, hidden-accepts sees the keyed match, "
                     "skip-head sees the tail match, always-exists is right because "
                     "a match exists). So this rival carries its own separating "
                     "input and pins existence-vs-uniqueness, which no other case "
                     "reaches.",
        "witness": _witness(
            "[{ key := 4, hidden := false }, { key := 4, hidden := true }]",
            "4", "false"),
    },
    {
        "id": "weak-magnitude-key",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Every shipped witness uses a NON-NEGATIVE target, so the
        # `target` binder was varied only over {0,3,5,7,9} and nothing pinned that
        # the comparison is signed equality on `Int` rather than equality of
        # magnitudes. This rival matches on |key| = |target|: identical to the
        # post-image on every non-negative input, wrong at a negative target.
        "module": _impl(
            "    return rows.any (fun r => r.key.natAbs == target.natAbs)"),
        "refinement": "a real patch whose comparison normalised the referenced "
                      "value before matching (dropping its sign) would validate a "
                      "reference to an identity that is NOT stored, whenever some "
                      "stored record carries the same value with the opposite sign "
                      "— a dangling reference accepted on any model whose "
                      "referenced field admits negative values. It fails the "
                      "reject-expecting validation tests on that input class while "
                      "passing every non-negative one; it would NOT resolve.",
        "rationale": "REJECT from `out = existsMatch target rows`: `matchesTarget` "
                     "is `r.key == target`, signed equality on `Int`, but the rival "
                     "compares magnitudes, so on a record whose key is the NEGATION "
                     "of the target the post-image demands `false` while the rival "
                     "returns `true`. Refuted at `[{key:=6,hidden:=false}]` with "
                     "`target=-6` — the only witness in this battery at a NEGATIVE "
                     "target, a sub-domain where every other rival here is correct "
                     "(no record's key equals -6, and none is hidden, so prepatch, "
                     "hidden-accepts, skip-head and never-exists all agree on "
                     "`false`). It varies the `target` binder off the non-negative "
                     "range the other five witnesses share and pins that the match "
                     "is signed equality, not equality up to sign.",
        "witness": _witness("[{ key := 6, hidden := false }]", "(-6)", "true"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation, 5 uniqueness) plus a 2-case AXIOM
# lane. This bundle models a NARROWER surface: the nagini sibling contracts a
# single function `validate_reference(value, complete_rows, curated_rows)` whose
# postcondition `reference_holds = present(value, complete_rows) AND
# choice_permitted(value)` conjoins an OPAQUE per-key predicate; this backend
# models only the existence test over the consulted collection
# (`out = existsMatch target rows`), with the everyday-vs-complete view difference
# captured by `Record.hidden` and the `limit_choices_to` narrowing dropped as a
# shared, unchanged pre/post-filter (mapping.md §2, §3). The accounting below
# records every sibling case.
#
#   sibling case            -> here                              disposition
#   -----------------------------------------------------------------------
#   pos-reorder-decision    -> pos-commute-disjunct              PORTED (reshaped)
#   admiss-reads            -> admiss-hidden-nondegenerate       RE-AIMED
#   frame-mut-complete      -> (none)                            VACUOUS
#   frame-mut-curated       -> (none)                            VACUOUS
#   weak-curated-bug        -> weak-prepatch-everyday-view       PORTED
#   weak-skip-head          -> weak-skip-head                    PORTED
#   weak-ignore-choice      -> (none)                            NO COUNTERPART
#   weak-always-return      -> weak-always-exists                PORTED
#   weak-always-raise       -> weak-never-exists                 PORTED
#   (no sibling)            -> pos-return-fold                   ADDED (2nd pos.)
#   (no sibling)            -> weak-hidden-accepts               ADDED (audit)
#   (no sibling)            -> weak-count-exactly-one            ADDED (audit 2)
#   (no sibling)            -> weak-magnitude-key                ADDED (audit 2)
#   AXIOM_TESTS (2)         -> (none)                            DROPPED (G-AX)
#
# 5 ported, 1 re-aimed, 2 vacuous, 1 with no counterpart on this carrier; 1 extra
# positive and 3 extra rivals added.
#
# ADDED (weak-count-exactly-one, weak-magnitude-key): found by the second audit
#   pass, which enumerated what the six existing witnesses hold FIXED rather than
#   what they vary. Two sub-domains were untouched by every case: the MATCH COUNT
#   (every witness had 0 or 1 matching record, so nothing distinguished the
#   existence OR-fold from a uniqueness test) and the SIGN of the compared values
#   (every target was non-negative, so nothing distinguished signed equality from
#   equality of magnitudes). Both rivals are rejected, each refuted at a point
#   where every OTHER rival in the battery is correct — the strongest form of
#   separation available here. Both witnesses were rebuilt out-of-band on all four
#   subjects: rival exit 0, frozen solution exit 1, and each of the two correct
#   reshapes exit 1 with leg (a) `rfl failed: not definitionally equal`, which is
#   what shows they are refuted for being WRONG and not merely for being loop-free.
#
# ADDED (weak-hidden-accepts): found by audit. Every original rival abused
#   `Record.hidden` in at most ONE direction — SUPPRESSING a keyed match
#   (`weak-prepatch-everyday-view`). Nothing pinned the converse, that `hidden` may
#   not MANUFACTURE a match: `matchesTarget` is `r.key == target` alone, so an impl
#   reading `matchesTarget target r || r.hidden` is wrong on a hidden record whose
#   key does not match. It is rejected, refuted at `[{key:=3,hidden:=true}]` /
#   `target=7`, a point where the prepatch rival is CORRECT. Its three-leg witness
#   was checked against the frozen solution (exit 1) and against `pos-return-fold`
#   (exit 1, leg (a) `rfl failed: not definitionally equal`).
#
# PORTED-RESHAPED (pos-commute-disjunct): the sibling's positive control reshapes
#   the final decision from `if not (found and choice): raise; return` into the
#   positive form. This backend has no raise/return fork (the observable is a
#   `Bool`, not control flow) and no `choice_permitted` conjunct, so the exact
#   reshape does not exist; the reshape SPIRIT — "structurally different,
#   behaviourally identical" — is carried by commuting the running disjunction in
#   the gold loop body (`||` commutative). Verified to build (proof retuned with
#   `Bool.or_comm`).
# ADDED (pos-return-fold): a second positive this backend affords — discard the
#   loop and return the pure existence fold directly. Guards against
#   SPEC-TOO-STRONG on the loop-vs-fold axis; the reproof is a bare `loom_solve`.
#   The sibling's inline loop does not have this axis. Verified to build.
# RE-AIMED (admissibility): the sibling's admissibility control asserts the pair
#   of half-permissions admits reading a normal input. This backend declares NO
#   `require` clause and has no permission surface, so that probe is degenerate
#   (every input is in-domain). It is re-aimed at the residual total-domain risk —
#   that the existence decision is DEGENERATE at the interesting point — via an
#   in-region assert that the fold yields `true` on a matching HIDDEN record,
#   `false` on the empty collection, and `false` on a non-matching record. Live
#   assert (a false claim leaves an unsolved `decide` goal — verified).
# PORTED (weak-prepatch-everyday-view): the sibling's `weak-curated-bug` decides
#   over the CURATED default collection instead of the COMPLETE one — the literal
#   pre-patch behaviour. On this carrier the two collections are ONE input `rows`
#   with the everyday-view exclusion recorded by `Record.hidden`, so "consult only
#   the curated view" is "consult only the non-hidden records"
#   (`matchesTarget target r && ! r.hidden`). Refuted at a matching HIDDEN record,
#   the F2P discriminator. This is the case the whole spec exists to sense.
# PORTED (weak-skip-head): direct port of the off-by-one head skip, expressed
#   straight-line as `(rows.drop 1).any ...`. Refuted at a two-record collection
#   whose head is the only match.
# PORTED (weak-always-exists / weak-never-exists): the sibling's cheapest
#   "forgot to do the work" baselines. `weak-always-return` (never raise = always
#   accept) ports to `return true` (always report a match); `weak-always-raise`
#   (always reject) ports to `return false` (never report a match). Refuted at the
#   empty collection and a single matching record respectively — two DISTINCT
#   points, each where the OTHER partial-domain rivals are correct.
# VACUOUS (frame-mut-complete, frame-mut-curated): the sibling's two MANDATORY
#   frame-mutation rivals keep the gold body verbatim then write back into a
#   read-only sequence input granted only at half permission, and must be rejected
#   for INSUFFICIENT PERMISSION. This backend is referentially transparent: every
#   parameter is an immutable value, the method declares no `mut` binder, there is
#   no heap and no aliasing. There is no read-only input to overwrite and no
#   permission system to trip, so the class is vacuous. No substitute is
#   fabricated (per the porting map: this class is vacuous on Lean/Velvet).
#   DEMONSTRATED rather than asserted, by an audit pass that tried to land the
#   rival anyway (three builds, all recorded out-of-band):
#     * writing the input inside the impl region — the only region surgery may
#       touch — is not a spec violation the verifier can weigh, it is a LANGUAGE
#       error: `rows := rows` fails to elaborate with "`rows` cannot be mutated,
#       only variables declared using `let mut` can be mutated" (exit 1). A rival
#       rejected for failing to PARSE attributes nothing to the spec, which is the
#       precise defect the witness requirement exists to catch;
#     * making the write legal instead requires `mut rows` in the SIGNATURE, which
#       is spec text: `same_spec` is False and `variant_scope` reports "spec view
#       differs", so the case is out of scope and the gate would record
#       `spec-changed` (a malformed test, not a finding).
#   So the class is not merely unattacked here, it is unattackable in-scope: the
#   mutation is either unparseable or a spec change. That is a carrier collapse,
#   not an effort gap.
# NO COUNTERPART (weak-ignore-choice): the sibling conjoins an OPAQUE
#   `choice_permitted(value)` (the field's `limit_choices_to` narrowing) as the
#   SECOND conjunct of `reference_holds` and rejects a rival that drops it. On this
#   carrier the `limit_choices_to` narrowing is applied IDENTICALLY by both
#   collection sources and is unchanged by the fix (mapping.md §2 Note, §3), so it
#   is NOT part of the modeled discriminator — the spec is `out = existsMatch
#   target rows`, which has no `choice_permitted` clause to attack. A rival that
#   "dropped the narrowing" would be indistinguishable from gold on this carrier
#   (the narrowing was never modeled), so no witness could refute it. Legitimately
#   omitted as carrier narrowing, NOT an effort gap — the modeled surface simply
#   does not carry the second conjunct the nagini spec did.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 7 distinct input
#   points):
#     rows        — [{7,hidden}] (prepatch); [{5},{0}] (skip-head);
#                   [] (always-exists); [{9}] (never-exists);
#                   [{3,hidden}] (hidden-accepts); [{4},{4,hidden}]
#                   (count-exactly-one); [{6}] (magnitude-key): length
#                   1/2/0/1/1/2/1, with a hidden record present in the three
#                   witnesses that turn on `hidden` and non-hidden elsewhere;
#                   keys {7,5,0,9,3,4,6} varied. MATCH COUNT is varied too:
#                   0 matches (always-exists), 1 (four witnesses), 2
#                   (count-exactly-one) — the last is what makes the OR-fold's
#                   monotonicity observable rather than assumed.
#     target      — 7 / 5 / 0 / 9 / 7 / 4 / -6: varied, and NOT a function of the
#                   key — `[{key:=3,hidden:=true}]` with `target=7` is the one
#                   witness where the target matches NO record's key while a record
#                   is hidden, which is what separates the two `hidden` directions;
#                   `-6` against a stored key of `6` is the one witness at a
#                   NEGATIVE target, which is what makes the comparison's SIGN
#                   observable (magnitude equality would agree everywhere else).
#     Record.hidden — true (prepatch, hidden-accepts, and the second record of
#                   count-exactly-one) vs false (the rest), and the two decisive
#                   hidden=true points are NOT two spellings of one point: at
#                   `[{7,true}]/7` the key MATCHES (the spec demands `true`, the
#                   prepatch rival wrongly says `false`), at `[{3,true}]/7` it does
#                   NOT (the spec demands `false`, the hidden-accepts rival wrongly
#                   says `true`). So `hidden` is pinned in both directions: it may
#                   neither suppress a keyed match nor manufacture one, which is
#                   exactly the independence of `matchesTarget` from `hidden`.
#     Record.key  — {7,5,0,9,3,4,6}: varied; the equality with `target` is what
#                   makes each match/non-match witness fire, and `6` vs `-6` is
#                   what makes it an equality rather than a magnitude comparison.
#   The sole top-level clause is attacked in BOTH directions (always-exists /
#   never-exists), on the hidden sub-domain in BOTH directions (prepatch — THE fix
#   — and hidden-accepts), on the traversal sub-domain (skip-head), on the
#   existence-vs-uniqueness axis (count-exactly-one), and on the sign of the
#   comparison (magnitude-key).
#
#   WHAT "SEPARATING INPUT" DOES AND DOES NOT MEAN HERE (an earlier revision of
#   this file overstated it, and the correction is the audit's main prose finding).
#   The two baselines are wrong EVERYWHERE their direction applies, so a point that
#   refutes a partial-domain rival usually refutes a baseline too. Enumerated over
#   the seven points: at `[{7,true}]/7` the prepatch rival is wrong AND so are
#   skip-head and never-exists; at `[{9,false}]/9` never-exists is wrong AND so is
#   skip-head. What each witness establishes is therefore NOT "only this rival
#   fails here" but "this rival fails here, and this rival agrees with the
#   post-image on the complement" — the partial-domain claim. The genuinely
#   exclusive points are `[]/0` (only always-exists), `[{3,true}]/7` (only
#   hidden-accepts and always-exists), `[{4},{4,true}]/4` (only count-exactly-one)
#   and `[{6}]/-6` (only magnitude-key).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no deep-model reference (the collection-source primitive is modeled
# deeply as `existsMatch`), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
