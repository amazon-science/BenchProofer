"""properties.py — G-PBT falsification battery for django__django-14053 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct reportCollected`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates).

DEFENDED SURFACE. One contracted method over a read-only stream of per-pass
observations ``events : List Obs`` (``Obs = Int × Int``: a source-item key paired
with a value observed for it). The method returns the sequence reported back to
the caller, and carries two load-bearing post-images:

  reportCollected (events)   ensures out = collect events
                             ensures (out.map Prod.fst).Nodup

``collect`` is the order-preserving keep-last collapse of the stream: every
distinct key appears exactly once, in first-encounter order, carrying its LAST
observed value. The second clause is the independent no-key-twice guarantee —
the property the failing test demands (no reported item recurs). ``events`` is
the sole INPUT BINDER; it is read-only (no ``mut``).

The clause structure is what the rival lane is built around, because the two
clauses are independently attackable and a rival can satisfy either alone:

  * ``Nodup`` alone is satisfied by any key-unique output, INCLUDING an empty
    one and including one carrying wrong VALUES;
  * ``out = collect events`` alone is the whole answer, but it decomposes into
    three independent sub-behaviors a rival can break one at a time — WHICH keys
    are reported, in WHAT ORDER, and WITH WHICH VALUE.

So the battery attacks the key SET (``weak-drop-all``, ``weak-drop-first``), the
key MULTIPLICITY (``weak-report-raw``, ``weak-collapse-adjacent-only``) and the
reported VALUE (``weak-keep-first-value``) separately. The value leg matters on
its own: a rival that gets keys, order and uniqueness all right and only reports
a STALE value satisfies ``Nodup`` outright and fails only the keep-last half of
the first clause. Without it, every reject witness could hold the pair's second
component constant and a value-only defect would sail through — the exact
masking failure this lane exists to prevent (see WITNESS PLACEMENT).

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the sibling
    because a read-only input may carry a fractional heap permission an impl can
    overwrite. This backend is referentially transparent: every parameter is an
    immutable value, there is no ``mut`` binder in this bundle, no heap and no
    aliasing — so there is no read-only input to mutate and no substitute probe
    to build. Not fabricated (see the module footer).
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
    loop in the impl (1 loop here, measure ``events.length - i``). A rival that
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
  * UNGROUNDED-ORACLE ECHO — N/A. Both post-images are total, fully unfolded
    functions of the method's own input (``collect``/``upsert``/``collectStep``
    are concrete ``def``s in the ``pure`` region; the ``axioms`` region is
    empty). There is no opaque answer key to echo — echoing ``collect`` IS the
    correct answer — so there is no WRONG echo to build. Honest cheapest-reshape
    positive controls (``pos-*``) stand in.
  * MULTIPLICITY — APPLIES: the sibling's central defect. Attacked twice, at two
    different strengths (see ``weak-collapse-adjacent-only``, the near-miss).
  * PARTIAL-DOMAIN / VALUE — APPLIES, three ways (key set, and reported value).

WITNESS MECHANICS on this carrier — and the one thing this port had to repair.
The frozen impl keeps a ``while`` loop, and under
``loom.semantics.choice "demonic"`` that loop's fixpoint elaborates through
``Classical.choice``, which the kernel cannot unfold. So ``decide`` against the
FROZEN solution is stuck for EVERY claim, true or false. Measured on this cell:

    witness  reportCollectedTester [(1,1),(1,1)] = false   vs frozen -> stuck
    OPPOSITE reportCollectedTester [(1,1)]       = true    vs frozen -> stuck

both failing with the identical ``did not reduce to `isTrue` or `isFalse` ``.
The frozen side's exit code therefore carries NO information, and a witness
refuted "against gold" here would attest to a refutation the kernel never
performed — including a forged one asserting the rival is CORRECT. That is the
``witness-undecided`` defect, and it is why every reject case below names a
``witness_reference``: the loop-free ``return collect events`` impl, which
implements the frozen spec CORRECTLY and DOES reduce. Against it each witness
fails with a real verdict — ``decide proved that the proposition ... is false``
— which is the discrimination the gate is asking for. The reference is also
shipped as an ``expect="verify"`` case (``pos-collapse-direct``) so the battery
itself records that loop-freeness is not what any rival is being rejected for.

WITNESS PLACEMENT. Five rivals, five DISTINCT input points, and no two share one:
each rival is refuted on the sub-domain its ``rationale`` actually claims.

  * ``weak-report-raw`` at ``[(1,1),(1,2)]`` — a repeated key. The only shape on
    which the no-key-twice clause can bite at all.
  * ``weak-collapse-adjacent-only`` at ``[(1,1),(2,2),(1,3)]`` — a NON-adjacent
    repeat. This rival is the sharper near-miss of ``weak-report-raw``: it does
    collapse repeats, just only adjacent ones, so it AGREES with the frozen
    report on every stream whose repeats are adjacent (including
    ``weak-report-raw``'s own point, where it is correct — checked). Refuting it
    at the raw rival's point would be impossible; it needs the interleaved shape,
    which is exactly the sub-domain its rationale claims.
  * ``weak-keep-first-value`` at ``[(2,8),(2,3)]`` — a repeated key whose value
    DECREASES, so the point also rules out a rival that happens to take the max
    rather than the last. Keys, order and uniqueness are all correct here; only
    the value is stale, so this refutation runs through the keep-last half of the
    first clause and nothing else.
  * ``weak-drop-first`` at ``[(1,5),(2,7)]`` — two DISTINCT keys, where it
    returns the tail while ``weak-drop-all`` returns empty: the point that
    SEPARATES the two near-misses rather than the singleton where they coincide.
  * ``weak-drop-all`` at ``[(1,9)]`` — the singleton, the smallest point that
    separates it from the frozen report.

The VALUE component is varied across the five points (1/2, 1/2/3, 8/3, 5/7, 9)
and is nowhere equal to its own key, so no rival could pass by confusing ``snd``
with ``fst`` or by holding the value fixed. Stream LENGTH varies 1..3, and both
the all-distinct and the repeated-key shapes are probed. pts = 5.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the one callee
involved is unchanged and supplies only the read-only input stream, owed no
contract). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14053"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the one impl region and is
# ---- unique inside Solution.lean; both facts asserted at load by _swap) ----

# The whole executable body: the accumulator loop that collapses the stream and
# returns it. Reshaped wholesale by the rivals and the straight-line positive.
_IMPL = (
    "    let mut result : List Obs := []\n"
    "    let mut i := 0\n"
    "    while i < events.length\n"
    "      invariant i ≤ events.length\n"
    "      invariant result = (events.take i).foldl collectStep []\n"
    "      done_with i = events.length\n"
    "      decreasing events.length - i\n"
    "    do\n"
    "      let e := events[i]!\n"
    "      result := upsert result e.1 e.2\n"
    "      i := i + 1\n"
    "    return result\n"
)

# The single loop-body step (a substring of _IMPL; unique in the file). Reshaped
# by the loop-preserving positive control.
_STEP = "      result := upsert result e.1 e.2\n"

# The accumulator initializer (unique). Anchor for the admissibility assert.
_INIT = "    let mut result : List Obs := []\n"

# ---- proof-body anchors. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a reshape may retune its tactic script without
# ---- touching the spec or dropping the obligation. ----

# The full frozen tactic script. Every variant that removes the loop also removes
# the loop-invariant goals this script closes, so it is retuned to a bare
# `loom_solve` there — never weakened, and the obligation's statement is
# untouched in every case.
_PROOF = (
    "prove_correct reportCollected by\n"
    "  loom_solve\n"
    "  case «invariant_2: result = (events.take i).foldl collectStep []» =>\n"
    "    have hi : i < events.length := by omega\n"
    "    rw [invariant_2, collect_take_step events i hi, collectStep,\n"
    "        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]\n"
    "  case «ensures_1: (out.map Prod.fst).Nodup» =>\n"
    "    have h := collect_nodup events\n"
    "    simp_all [collect]\n"
    "  all_goals simp_all [collect]"
)
_BARE_PROOF = "prove_correct reportCollected by\n  loom_solve"

# The final catch-all tactic line (unique; retuned by the admissibility case to
# also discharge the in-region assert's concrete goal).
_PROOF_TAIL = "  all_goals simp_all [collect]"


def _straight(body):
    """A loop-free variant: `body` as the whole impl, proof retuned to loom_solve.

    Retuning is mandatory, not a convenience: the frozen tail proves goals about
    the frozen LOOP's invariants, which a loop-free body does not raise at all
    (`No goals to be solved`). Only the tactic body moves — the `prove_correct`
    header and the method's `ensures` clauses stay byte-identical.
    """
    return _swap(_swap(_BASE, _IMPL, body), _PROOF, _BARE_PROOF)


# ---- the witness_reference: a CORRECT, loop-free impl of the frozen spec.
# ---- Returns the modeled collapse directly, so it verifies (checked by the gate
# ---- before use) AND reduces under `decide`, which the frozen loop does not.
# ---- Shipped as `pos-collapse-direct` too, so the battery records that
# ---- loop-freeness is not what any rival is rejected for.
_LOOPFREE = _straight("    return collect events\n")


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery:
# ---- `reportCollectedTester <stream> = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict. There is no `require` clause, so the
# ---- precondition is `True` and decides trivially. Every point below is a
# ---- concrete small literal, so nothing is conditioned on and there are no
# ---- hypotheses that could be jointly unsatisfiable.
_TESTER = (
    "extract_program_for reportCollected\n"
    "prove_precondition_decidable_for reportCollected\n"
    "prove_postcondition_decidable_for reportCollected\n"
    "derive_tester_for reportCollected\n\n"
)


def _witness(point):
    return _TESTER + (f"example : reportCollectedTester {point} = false := by\n"
                      "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps both obligations with a
    # byte-identical statement; only the executable surface and (where the
    # reshape removes the loop) the tactic script move.
    # =====================================================================
    {
        "id": "pos-step-rephrased",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the loop body folds one observation through the named
        # per-step combinator instead of spelling the keyed upsert inline. Same
        # accumulator, same order, so both post-images still hold and the frozen
        # loop-invariant proof discharges unchanged.
        "module": _swap(_BASE, _STEP, "      result := collectStep result e\n"),
        "rationale": "a correct reshape of the loop body (folding through the "
                     "per-step combinator) computes the same accumulator, so "
                     "both `out = collect events` and `(out.map Prod.fst).Nodup` "
                     "still discharge with the frozen invariants; must verify "
                     "else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-collapse-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the loop entirely and return the modeled collapse
        # directly. Observationally identical (the loop's post-state IS the
        # collapse), so both clauses hold. This is also the `witness_reference`
        # every reject case below is refuted against, and it is shipped as its
        # own case so that its verifying status is recorded by the battery
        # rather than merely assumed by the reject lane.
        "module": _LOOPFREE,
        "rationale": "returning the modeled collapse directly satisfies "
                     "`out = collect events` definitionally and "
                     "`(out.map Prod.fst).Nodup` by the collapse's own "
                     "uniqueness lemma; a correct loop-free reshape must verify "
                     "(else SPEC-TOO-STRONG on the loop form). Doubles as the "
                     "reject lane's witness_reference, so this case failing "
                     "would invalidate that lane rather than pass quietly.",
    },

    # =====================================================================
    # ADMISSIBILITY. No method here has a `require` clause, so there is no
    # precondition that could exclude a normal input; the usual "a normal
    # input satisfies the precondition" probe is vacuous. The residual
    # admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE / DEGENERATE at the interesting point — a spec no impl can
    # meet reads exactly like a spec every impl meets. This case discharges an
    # in-region `assert` that pins the collapse's discriminating behavior at a
    # concrete repeated-key stream: the last value wins, the earlier one is
    # dropped, and the reported keys are unique. The surrounding impl is kept
    # verbatim so the method's own obligations still discharge; the assert is
    # live (a false claim about the same point leaves an unsolved goal).
    # =====================================================================
    {
        "id": "admiss-keeplast-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _INIT,
                "    assert (with_name_prefix `assert\n"
                "      (collect [(1, 1), (1, 2)] = [(1, 2)] ∧\n"
                "       ((collect [(1, 1), (1, 2)]).map Prod.fst).Nodup))\n"
                + _INIT),
            _PROOF_TAIL,
            "  all_goals first | (refine ⟨by decide, by decide⟩) "
            "| simp_all [collect]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "interesting point: on a repeated-key stream the modeled "
                     "collapse keeps the LAST value (dropping the earlier one) "
                     "and reports the key once. The in-region assert must "
                     "discharge (else the obligation is degenerate); the impl is "
                     "kept verbatim so both ensures clauses still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is written
    # loop-free so ITS tester reduces under `decide`; each is refuted against
    # the loop-free CORRECT reference rather than against the frozen loop,
    # which cannot decide anything (see WITNESS MECHANICS).
    # =====================================================================
    {
        "id": "weak-report-raw",
        "kind": "uniqueness",
        "expect": "reject",
        # The multiplicity defect: report the stream raw, with NO collapse. A
        # key observed in more than one pass is reported once per observation.
        "module": _straight("    return events\n"),
        "witness": _witness("[(1, 1), (1, 2)]"),
        "witness_reference": _LOOPFREE,
        "refinement": "a counterpart that reports the stream raw re-emits a "
                      "source item once per pass, so an item observed across "
                      "several passes is reported multiple times — exactly the "
                      "duplication the failing test forbids (it asserts no "
                      "reported item recurs). It would NOT resolve.",
        "rationale": "REJECT from BOTH clauses: on a repeated-key stream the raw "
                     "report lists that key more than once, so "
                     "`(out.map Prod.fst).Nodup` fails, and `out = collect "
                     "events` fails since the collapse would list it once. "
                     "Refuted on the repeated-key stream — the only shape on "
                     "which the no-key-twice clause bites.",
    },
    {
        "id": "weak-collapse-adjacent-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The sharper near-miss of weak-report-raw: it DOES collapse repeats,
        # but only when they are ADJACENT in the stream. A key whose
        # observations are separated by another key's observation is still
        # reported twice. Agrees with the frozen report on every
        # adjacent-repeat stream, so it is only refutable on the interleaved
        # shape.
        "module": _straight(
            "    return events.foldl (fun m e => "
            "if m ≠ [] ∧ (m.getLast! : Obs).1 = e.1 "
            "then m.dropLast ++ [e] else m ++ [e]) []\n"),
        "witness": _witness("[(1, 1), (2, 2), (1, 3)]"),
        "witness_reference": _LOOPFREE,
        "refinement": "a counterpart that only merges an item with the one "
                      "reported immediately before it still re-emits any item "
                      "whose observations are separated by another item's — the "
                      "ordinary case once more than one item is being reported "
                      "per pass. That recurrence is what the failing test's "
                      "no-duplicate assertion catches. It would NOT resolve.",
        "rationale": "REJECT from both clauses, but only on the NON-adjacent "
                     "repeat sub-domain: this rival AGREES with the frozen "
                     "report whenever a key's observations are adjacent "
                     "(including weak-report-raw's own point, where it is "
                     "correct), so it is refuted at the interleaved stream "
                     "[(1,1),(2,2),(1,3)] where it reports key 1 twice. This is "
                     "the near-miss that shows the multiplicity clause is "
                     "load-bearing beyond the trivial no-collapse rival.",
    },
    {
        "id": "weak-keep-first-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-only defect: the right keys, the right order, and full
        # key-uniqueness — but a key that recurs keeps its FIRST observed value
        # instead of its last. Satisfies the Nodup clause outright, so it can
        # only be refuted through the keep-last half of the exact-report clause.
        "module": _straight(
            "    return events.foldl (fun m e => "
            "if e.1 ∈ m.map Prod.fst then m else m ++ [(e.1, e.2)]) []\n"),
        "witness": _witness("[(2, 8), (2, 3)]"),
        "witness_reference": _LOOPFREE,
        "refinement": "a counterpart that keeps the FIRST value observed for a "
                      "recurring item reports that item once (so the "
                      "no-duplicate assertion passes) but reports it with a "
                      "stale intermediate value rather than the final one the "
                      "later passes established. The reported value is what the "
                      "caller records and re-checks for consistency afterwards, "
                      "and the issue states the final value is the one expected, "
                      "so it would NOT resolve.",
        "rationale": "REJECT from `out = collect events` ALONE — specifically "
                     "its keep-last half. `(out.map Prod.fst).Nodup` is "
                     "SATISFIED by this rival (each key appears once, in "
                     "first-encounter order), which is why the case matters: it "
                     "is the only rival that forces the second component of Obs "
                     "to be observed. Refuted at [(2,8),(2,3)], where the value "
                     "DECREASES, so the point also excludes a rival that takes "
                     "the max rather than the last.",
    },
    {
        "id": "weak-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: the collapse is correct, but the first reported item is
        # dropped. Key-uniqueness still holds (dropping from a unique-key list
        # keeps it unique), so ONLY the exact-sequence clause is attacked.
        "module": _straight("    return (collect events).drop 1\n"),
        "witness": _witness("[(1, 5), (2, 7)]"),
        "witness_reference": _LOOPFREE,
        "refinement": "a counterpart that omits the first reported item leaves "
                      "that item's name out of the reported set, so the failing "
                      "test's membership assertion for it fails on any stream "
                      "with at least one reported item. It would NOT resolve.",
        "rationale": "REJECT from `out = collect events`: on any non-empty "
                     "reported sequence the impl drops the first entry the "
                     "post-image requires. Key-uniqueness still holds, so this "
                     "attacks the exact-sequence clause alone. Refuted on a "
                     "two-distinct-key stream, where it returns the tail while "
                     "weak-drop-all returns empty — the point that SEPARATES the "
                     "two near-misses.",
    },
    {
        "id": "weak-drop-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Reports nothing: correct only on the empty stream, drops every
        # reported item otherwise. Key-uniqueness holds vacuously.
        "module": _straight("    return []\n"),
        "witness": _witness("[(1, 9)]"),
        "witness_reference": _LOOPFREE,
        "refinement": "a counterpart that reports nothing surfaces no item's "
                      "name at all, so every membership assertion in the failing "
                      "test fails. It would NOT resolve.",
        "rationale": "REJECT from `out = collect events`: on any non-empty "
                     "stream the impl reports the empty sequence where the "
                     "post-image demands the collapse. Correct only on the empty "
                     "stream — and it shows the Nodup clause cannot carry the "
                     "spec alone, since it holds vacuously here. Refuted on the "
                     "singleton, the smallest point that separates it from the "
                     "frozen report.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 cases (1 soundness
# positive, 1 admissibility, 1 mandatory frame-mutation, 3 uniqueness rivals);
# every one is accounted for below. The sibling contracts a single function
# `collect_reports(ids, adj)` over two aligned streams (plain ids, adjustable
# ids); this bundle contracts a single method `reportCollected(events)` over the
# flattened stream of per-pass observations, since the pass-through legs carry no
# discriminating behavior under either the pre- or post-change behavior
# (mapping.md §3.3). The map is stated case by case.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder            -> pos-step-rephrased            PORTED
#   admissibility-normal-input            -> admiss-keeplast-nondegenerate RE-AIMED
#   frame-mutation-write-readonly-ids     -> (none)                        VACUOUS
#   uniqueness-adjustable-reported-twice  -> weak-report-raw               PORTED
#   partial-domain-drop-all-adjustable    -> weak-drop-all                 PORTED
#   partial-domain-drop-first-adjustable  -> weak-drop-first               PORTED
#
# 4 ported, 1 re-aimed, 1 vacuous = 6. ADDED, with no sibling counterpart:
#   * pos-collapse-direct          — a loop-free correct reshape, defending both
#     clauses from a second structural angle, and the reject lane's reference.
#   * weak-collapse-adjacent-only  — the near-miss of the multiplicity rival.
#     The sibling's carrier cannot express it (its two streams are collapsed by
#     construction, never interleaved), but this carrier can, and without it the
#     multiplicity clause is only ever probed by a rival that does no collapsing
#     at all.
#   * weak-keep-first-value        — the VALUE leg. The sibling's carrier models
#     only WHICH ids are reported (`ids`/`adj` are id streams, so there is no
#     reported value to get wrong); this carrier pairs each key with a value and
#     the frozen spec pins keep-last, so a rival can be right about every key and
#     still wrong. This is the clause a key-only battery would leave untested.
#
# RE-SITED (a note, not a separate class): the sibling separates the two
#   sub-streams and its rivals permute or drop within their concatenation. Here
#   the modeled stream `events` is the observation stream and the collapse is its
#   keep-last dedup, so uniqueness-adjustable-reported-twice becomes "report the
#   stream raw" (weak-report-raw), drop-all-adjustable becomes "report nothing"
#   (weak-drop-all), and drop-first-adjustable becomes "drop the first reported
#   item" (weak-drop-first). The ARGUMENT is unchanged in each; only the carrier
#   is. The sibling's own note that an ORDER-swap would RESOLVE the F2P (which
#   checks no duplicate and membership, not report order) is respected here too:
#   no order-only rival is shipped, since its faithful patch would resolve and
#   the case would be a verify-implies-resolve artifact rather than a defect.
# RE-AIMED (admissibility): the sibling establishes a precondition for a normal
#   input. No method here has a `require` clause, so that probe is vacuous. It is
#   re-aimed at the residual admissibility risk on a total domain — that the
#   post-image is degenerate at the interesting point.
# VACUOUS (frame-mutation): the sibling's MANDATORY read-only-input probe writes
#   into an input held at a fractional heap permission. This backend is
#   referentially transparent and this bundle declares no `mut` binder at all, so
#   there is no read-only input to overwrite and no substitute probe exists. Not
#   fabricated (spec_guide directive 5: the frame obligation here is discharged by
#   the ABSENCE of a `mut` on `events`, which the frozen spec already encodes).
#
# ---------------------------------------------------------------------------
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
#   loop in the impl (1 loop here, measure ``events.length - i``). A rival that
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
# RETRACTED IN FULL (what stood here before). The lines below this point used to
# carry the opposite disposition: that this bundle sets
# `loom.semantics.termination "partial"`, that a postcondition is therefore claimed
# only of TERMINATING runs, that a diverging prefix spliced at the top of the impl
# region VERIFIES at exit 0 "<- the hole", that the break is corpus-wide across a
# `partial` majority against a `total` minority, and that closing it would require
# editing the frozen Solution.lean. Every one of those is false of this artifact.
# Line 4 of the frozen file reads `"total"` and line 7 opens `TotalCorrectness`;
# all 500 velvet bundles do, and none sets `partial`. The diverging prefix is
# REJECTED, and so is the sharper rival that supplies a constant measure, which
# fails on the measure's own descent goal. Nothing needs closing and nothing is
# escalated. The correct disposition is the DIVERGENCE block immediately above,
# which records the builds; this notice is kept, rather than the text simply
# deleted, so a reader who saw the earlier claim can see it withdrawn.
#
# ---------------------------------------------------------------------------
# WITNESS ACCOUNTING. Five rivals, five distinct points of the sole binder
#   `events`, each chosen for the sub-domain that rival's rationale claims:
#     weak-report-raw               [(1,1),(1,2)]          repeated key
#     weak-collapse-adjacent-only   [(1,1),(2,2),(1,3)]    NON-adjacent repeat
#     weak-keep-first-value         [(2,8),(2,3)]          stale value, decreasing
#     weak-drop-first               [(1,5),(2,7)]          two distinct keys
#     weak-drop-all                 [(1,9)]                singleton
#   The value component varies (1/2, 1/2/3, 8/3, 5/7, 9) and never equals its own
#   key, so a rival confusing the pair's components, or one wrong only about the
#   value, cannot hide. Length varies 1..3; both all-distinct and repeated-key
#   shapes are probed; both clauses are attacked, and each is attacked by a rival
#   that satisfies the OTHER one (weak-keep-first-value satisfies Nodup;
#   weak-drop-all satisfies it vacuously). pts = 5.
#
#   Every witness is refuted against `witness_reference` = the loop-free correct
#   impl, NOT against the frozen solution, because the frozen loop's
#   `Classical.choice` fixpoint makes `decide` stuck for every claim and its exit
#   code would attest to nothing (see WITNESS MECHANICS in the docstring). The
#   gate independently checks that reference shares the frozen spec and VERIFIES
#   before trusting it, and it is shipped as `pos-collapse-direct` besides.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom, so there is nothing there to probe.
AXIOM_TESTS = []
