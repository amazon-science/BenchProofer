"""properties.py — G-PBT falsification battery for django__django-16100 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct processBatch`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates — the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a finite batch of queued record
updates). The single obligation is

    processBatch (updates : List Upd)  ensures out = committedAtomic updates

with ``committedAtomic us = if anyFail us then [] else changedVals us``: a batch
is one unit of work — if processing ANY row signals an error, the result must
commit NOTHING (every staged write is rolled back, so a mid-batch failure leaves
no partial progress); only a batch processed end-to-end without error commits
its edited rows' writes. ``updates`` is the sole input binder; each ``Upd``
carries ``changed`` (was this row actually edited), ``value`` (the write it would
persist — an opaque identity token) and ``raises`` (does processing this row
signal an error). The load-bearing content is that the failure verdict is
BATCH-GLOBAL: a failure anywhere discards EVERY replacement, with no committed
prefix.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini because
    a read-only input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: ``updates`` is an
    immutable value (declared read-only, not ``mut``), there is no heap and no
    aliasing, so there is no read-only input to mutate and no substitute probe
    to build. Not fabricated — reported as an omission in the footer.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    function of the method's own argument (``committedAtomic`` / ``anyFail`` /
    ``changedVals`` are concrete ``def``s in the ``pure`` region; the ``axioms``
    region declares nothing). There is no opaque answer key to echo, so there is
    no wrong echo to build; it is replaced by honest cheapest-reshape POSITIVE
    controls (``pos-*``).
  * PARTIAL-DOMAIN / COMMITTED-PREFIX — the heart of this instance. A rival that
    is right on the all-success sub-domain but leaves a committed prefix (or
    commits a privileged row) on the mid-failure sub-domain. Refuted at a failing
    batch, exactly where the desired behaviour and the pre-image diverge.
  * VERDICT POLARITY — a rival that inverts the commit/rollback decision.

WITNESS MECHANICS (specific to this carrier). The frozen impl keeps a ``while``
loop, and under ``loom.semantics.choice "demonic"`` its fixpoint elaborates
through ``Classical.choice``, which the kernel cannot unfold. So ``decide``
against the FROZEN tester is stuck for EVERY claim, true or false, and the
frozen side's exit code discriminates nothing. Measured here, and it is why an
earlier revision of this battery was wrong: the real witness

    processBatchTester [{changed := true, value := 9, raises := false},
                        {changed := true, value := 5, raises := true}] = false

and its exact OPPOSITE (``= true``, which asserts the rival is CORRECT at that
point) BOTH failed against the frozen solution with the identical
``did not reduce to `isTrue` or `isFalse` ``. A witness whose second half rests
on that exit code attests to a refutation the kernel never performed — so
"reshaping every rival loop-free makes the frozen side fail structurally" is NOT
a discrimination argument, and it is not the one made here.

The repair is ``witness_reference``: every reject case names ``_LOOPFREE`` — a
loop-free impl of the SAME frozen spec — as the subject its witness is refuted
against instead of gold. That is sound for the reason gold was: an impl the
verifier accepts cannot violate its own spec, so a genuine "the spec is violated
at this input" claim must fail there. And it is checked, not asserted:
``_LOOPFREE`` shares the frozen spec and VERIFIES (it also ships as the
``pos-atomic-closed-form`` positive, so the battery itself records that
loop-freeness is not what any rival is rejected for).

Verified by real builds, per rival: the witness ELABORATES against the rival
(exit 0) and FAILS against ``_LOOPFREE`` by actually DECIDING the claim false
(exit 1, no stuck-reduction message) — and ``_LOOPFREE`` decides the opposite
claim ``= true`` green, which is the control proving its tester really reduces.

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. The four rejects probe four DISTINCT input points, so the
single input binder ``updates`` is genuinely varied rather than pinned:
committed-prefix at a two-row batch whose second row fails; first-row-commits at
a one-row failing batch; verdict-flip at a one-row failing batch with a distinct
value; rollback-all at a one-row all-success batch (the only reject on the
SUCCESS branch of ``committedAtomic``, where the others agree with gold).

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the unchanged
commit/rollback machinery is an A-reference validated by axiom_check.py (G-AX's
job), not a consumed contract. There is no axiom-soundness obligation to probe
here, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16100"
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

# The WHOLE executable body of the method: the accumulating loop plus the commit
# point. Reject rivals replace this with a closed form (so their tester reduces).
_IMPL_BODY = """    -- All staged writes accumulate in one unit of work (`staged`); `failed`
    -- records whether processing any row signalled an error escaping that unit.
    let mut staged : List Int := []
    let mut failed : Bool := false
    let mut i : Nat := updates.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ updates.length
      invariant staged = changedVals (updates.drop i)
      invariant failed = anyFail (updates.drop i)
      done_with i = 0
      decreasing i
    do
      let u := updates[i - 1]!
      -- an edited row stages its write into the unit of work; a downstream step
      -- may signal a failure of the unit while processing that row.
      staged := (if u.changed then [u.value] else []) ++ staged
      failed := (u.changed && u.raises) || failed
      i := i - 1
    -- Commit point: a clean unit commits its staged writes; a failed unit
    -- commits nothing (the whole batch is rolled back as one unit of work).
    let committed : List Int := if failed then [] else staged
    return committed"""

# The two per-row assignments inside the loop body. They read disjoint state
# (`staged` and `failed` never depend on each other's new value), so swapping
# them is observationally identical and the frozen proof still closes.
_TWO_ASSIGN = """      staged := (if u.changed then [u.value] else []) ++ staged
      failed := (u.changed && u.raises) || failed"""

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = """    -- All staged writes accumulate in one unit of work (`staged`); `failed`
    -- records whether processing any row signalled an error escaping that unit.
    let mut staged : List Int := []"""

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). A positive control that collapses the loop to a closed form retunes
# this to `loom_solve`; the tactic body is elided from the spec view, so this is
# a proof reshape, not a spec change.
_PROOF_BODY = """  loom_solve <;>
    first
    | -- loop-entry: drop updates.length = [], both folds are nil.
      (rw [List.drop_length]; simp)
    | -- loop-body step: peel row `i-1` from the staged-values fold.
      (rw [changedVals_drop_step updates i (by omega) (by omega)]; simp_all)
    | -- loop-body step: peel row `i-1` from the error scan.
      (rw [anyFail_drop_step updates i (by omega) (by omega)]; simp_all)
    | -- exit (i = 0): `drop 0 = updates`, so the commit equals `committedAtomic`.
      (simp only [committedAtomic] at *; simp_all)"""

# The `first` alternation head, so the admissibility assert can add one arm.
_PROOF_FIRST = "  loom_solve <;>\n    first"


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery:
# ---- `processBatchTester args = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict.
_TESTER = (
    "extract_program_for processBatch\n"
    "prove_precondition_decidable_for processBatch\n"
    "prove_postcondition_decidable_for processBatch\n"
    "derive_tester_for processBatch\n\n"
)


# ---- THE WITNESS REFERENCE. A loop-free impl of the frozen spec whose extracted
# ---- tester kernel-REDUCES, so it can serve as the second subject of every
# ---- witness. The frozen impl cannot: its `while` fixpoint goes through
# ---- `Classical.choice`, leaving `decide` stuck for every claim (see the module
# ---- docstring), which is an outcome that discriminates nothing. Named by each
# ---- reject case as `witness_reference`; the gate independently checks it shares
# ---- the frozen spec and VERIFIES before trusting it, and it is ALSO shipped as
# ---- the `pos-atomic-closed-form` positive below so the battery records that
# ---- loop-freeness is not the reason any rival is rejected.
_LOOPFREE = _swap(
    _swap(_BASE, _IMPL_BODY, "    return (committedAtomic updates)"),
    _PROOF_BODY, "  loom_solve",
)


def _upd(changed, value, raises):
    c = "true" if changed else "false"
    r = "true" if raises else "false"
    return f"{{changed := {c}, value := {value}, raises := {r}}}"


def _witness(rows):
    batch = "[" + ", ".join(_upd(*r) for r in rows) + "]"
    return (_TESTER +
            f"example : processBatchTester {batch} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = committedAtomic
    # updates` obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-atomic-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) that computes the same commit set; the loop-specific proof
        # is retuned to a bare `loom_solve` since the impl now matches the
        # post-image syntactically. This is the SAME source every reject case
        # names as its `witness_reference`, shipped here as a case in its own
        # right so the battery records that this impl VERIFIES — i.e. that
        # loop-freeness is not what any rival is being rejected for.
        "module": _LOOPFREE,
        "rationale": "a loop-free impl that returns the commit set directly must "
                     "satisfy `out = committedAtomic updates`; a correct reshape "
                     "of the modeled behaviour verifying is exactly what "
                     "SPEC-TOO-STRONG would deny. Doubles as the witness "
                     "reference: the reject lane is refuted against this impl "
                     "(gold's loop cannot decide), so its verifying here is what "
                     "licenses that use.",
    },
    {
        "id": "pos-body-assign-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: swap the two per-row assignments in the loop body. They read
        # disjoint state, so the accumulator and the failure flag end each step
        # with the same values; the frozen proof still closes untouched.
        "module": _swap(
            _BASE, _TWO_ASSIGN,
            "      failed := (u.changed && u.raises) || failed\n"
            "      staged := (if u.changed then [u.value] else []) ++ staged"),
        "rationale": "the failure flag and the staged-writes accumulator update "
                     "from disjoint state, so reordering their per-row "
                     "assignments computes the same commit set; a correct "
                     "reshape must still satisfy `out = committedAtomic updates`.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has no `require` clause, so the domain is
    # total and no precondition could exclude an F2P-shaped input; the usual
    # "a normal input satisfies the precondition" probe is vacuously met. The
    # residual admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE / DEGENERATE at the interesting point — a spec no impl can
    # meet reads exactly like a spec every impl meets. So this case discharges
    # an in-region assert at the two-row F2P-shaped batch, establishing that the
    # post-image really does demand an empty commit set when a row fails midway
    # AND the full replacement set when the batch is clean. The surrounding impl
    # is kept verbatim so the method's own obligation still discharges; the
    # assert is live (a false claim about the same point leaves an unsolved
    # goal), and the proof's `first` alternation gains one `decide` arm to close
    # the ground assert.
    # =====================================================================
    {
        "id": "admiss-atomic-boundary",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_TOP,
                "    assert (with_name_prefix `assert\n"
                "      (committedAtomic [{changed := true, value := 9, raises := false},\n"
                "                        {changed := true, value := 5, raises := true}] = [] ∧\n"
                "       committedAtomic [{changed := true, value := 9, raises := false},\n"
                "                        {changed := true, value := 5, raises := false}] = [9, 5]))\n"
                + _IMPL_TOP),
            _PROOF_FIRST, "  loom_solve <;>\n    first\n    | decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped two-row batch: it demands the EMPTY commit set "
                     "when the second row fails (both writes revert, no committed "
                     "prefix) and BOTH writes when the batch is clean. The "
                     "in-region assert must discharge (else the obligation is "
                     "unsatisfiable / PRECOND-TOO-STRONG), and the impl is kept "
                     "verbatim so `out = committedAtomic updates` still verifies "
                     "too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-committed-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # Commits the writes of every row up to (but not including) the first
        # failing row — a committed prefix — instead of rolling the whole batch
        # back. This is the pre-image behaviour: no single unit of work, so a
        # failure midway leaves earlier writes already committed.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "    return (changedVals "
            "(updates.takeWhile (fun u => !(u.changed && u.raises))))"),
        "refinement": "a counterpart that keeps the writes made before a "
                      "mid-batch failure leaves a committed prefix: on the "
                      "scenario where an earlier row is processed cleanly and a "
                      "later row fails, the earlier row's replacement stays "
                      "persisted, but the failing tests assert every original "
                      "value is preserved. It would NOT resolve.",
        "rationale": "REJECT from `out = committedAtomic updates`: at a batch "
                     "whose first row is clean and second fails, the post-image "
                     "demands `[]` (batch-global rollback) while the impl commits "
                     "the clean prefix.",
        "witness": _witness([(True, 9, False), (True, 5, True)]),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-first-row-commits",
        "kind": "uniqueness",
        "expect": "reject",
        # Special-cases the FIRST row: its write is committed unconditionally,
        # only the tail is subject to the all-or-nothing verdict. Correct on the
        # all-success domain, wrong whenever the batch fails and the first row
        # was edited.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "    return (match updates with\n"
            "      | []      => []\n"
            "      | u :: us => (if u.changed then [u.value] else []) "
            "++ committedAtomic us)"),
        "refinement": "a counterpart that persists the first edited row's write "
                      "unconditionally leaves that row's replacement committed on "
                      "a batch that fails, but the failing tests assert the first "
                      "row's original value is preserved after a failure. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = committedAtomic updates`: at a one-row "
                     "batch whose only row is edited and fails, the post-image "
                     "demands `[]` while the impl commits that row's write.",
        "witness": _witness([(True, 9, True)]),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-verdict-flip",
        "kind": "uniqueness",
        "expect": "reject",
        # Inverts the commit/rollback polarity: commits the staged writes exactly
        # when the batch FAILED, and commits nothing when it succeeded.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "    return (if anyFail updates then changedVals updates else [])"),
        "refinement": "a counterpart that commits precisely when the batch failed "
                      "persists every replacement on the failure path, but the "
                      "failing tests assert originals are preserved when a row "
                      "raises. (It also commits nothing on a clean batch.) It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = committedAtomic updates`: on a failing "
                     "batch the post-image demands `[]` and the impl commits the "
                     "staged writes (flipped polarity).",
        "witness": _witness([(True, 5, True)]),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-rollback-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Commits NOTHING, ever — the SUCCESS branch of committedAtomic is the
        # one this attacks. The only reject probing a clean batch: the three
        # rivals above all agree with the frozen solution here (each commits the
        # full replacement set on an all-success batch), so this is where the
        # spec's dependence on the success branch is demonstrated.
        "module": _swap(_BASE, _IMPL_BODY, "    return []"),
        "refinement": "a counterpart that never commits any write discards a "
                      "clean batch's replacements, so the pre-existing "
                      "list-editable save assertions (which persist edits on a "
                      "batch with no failure) break. It would NOT resolve.",
        "rationale": "REJECT from `out = committedAtomic updates`: on a clean "
                     "one-row edited batch the post-image demands that row's "
                     "write and the impl returns `[]`. Refuted on the SUCCESS "
                     "branch — the sub-domain the other three rivals agree with "
                     "gold on — so the battery moves `updates` off the failure "
                     "path rather than pinning it there.",
        "witness": _witness([(True, 5, False)]),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1
# soundness positive, 1 admissibility, 4 uniqueness rivals) plus 1 AXIOM_TESTS
# entry. The sibling contracts the SAME single functional core this bundle
# models (a batch processed under all-or-nothing commit semantics), so the port
# is a near-1:1 re-expression against this carrier — not a carrier-narrowing
# drop — with the frame-mutation rival legitimately vacuous here.
#
#   sibling case                    -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-branch-reorder      -> pos-body-assign-reordered      PORTED
#   (—)                             -> pos-atomic-closed-form         ADDED
#   admiss-f2p-witness              -> admiss-atomic-boundary         RE-AIMED
#   frame-mutate-original           -> (none)                         VACUOUS
#   partial-prefix-local-verdict    -> weak-committed-prefix          PORTED
#   partial-first-row-always-commit -> weak-first-row-commits         PORTED
#   support-verdict-flip            -> weak-verdict-flip              PORTED
#   (—)                             -> weak-rollback-all              ADDED
#
# PORTED (4): the three failure-path rivals (committed prefix, first-row commit,
#   verdict flip) are the faithful re-expression of the sibling's partial-domain
#   and polarity rivals. Their refinement arguments carry over verbatim in
#   spirit: each commits something on a mid-batch failure (a committed prefix, a
#   privileged first row, or the whole batch on the flipped verdict), which is
#   exactly what the failing tests catch by asserting every original value is
#   preserved. The sibling's soundness positive (branch reorder) ports to the
#   body-assignment reorder, the closest loop-preserving correct reshape here.
# ADDED (2): pos-atomic-closed-form defends the obligation from a maximally
#   different control-flow shape (loop-free), and weak-rollback-all is the only
#   rival on the SUCCESS branch of committedAtomic — without it every reject
#   would sit on the failure path and the spec's dependence on the clean-batch
#   behaviour would go undemonstrated. Its faithful counterpart fails the
#   pre-existing list-editable save assertions rather than the specific
#   atomicity test, so it is a real would-not-resolve rival, not a fabrication.
# RE-AIMED (admissibility): the sibling establishes the precondition for a
#   normal input via an inline self-call. This method has no `require` clause,
#   so that probe is vacuous. It is re-aimed at the residual total-domain risk —
#   that the post-image is unsatisfiable/degenerate at the F2P-shaped point — by
#   discharging an in-region assert that the commit set is empty on the two-row
#   failing batch and the full replacement set on the clean one.
# VACUOUS (frame-mutation): the sibling's mandatory frame-mutation rival writes
#   to a half-permission read-only input. This backend is referentially
#   transparent and the modeled method declares no `mut` binder, so there is no
#   read-only input to overwrite and no substitute probe. Omitted as vacuous,
#   NOT fabricated.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates
#   the commit/rollback A-reference against the real transaction manager); the
#   commit semantics are modeled deeply here with no consumed axiom, and this
#   gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has a single input binder,
#   `updates : List Upd`, and a single top-level clause, `out = committedAtomic
#   updates`. The four reject witnesses probe four DISTINCT input points (a
#   two-row batch with a failing tail; two one-row failing batches with distinct
#   values; a one-row clean batch), so `updates` is genuinely varied and both
#   branches of committedAtomic are attacked (three on the failure branch, one
#   on the success branch). The `Upd.changed` field is `true` in every reject
#   witness on purpose: a rival that mishandled unedited rows keeps the correct
#   all-or-nothing verdict, so its faithful counterpart still preserves originals
#   on a failure and would resolve the atomicity test — it is not a
#   would-not-resolve rival. That sub-domain is defended positively instead, by
#   the closed-form positive control and the admissibility boundary assert.
# WITNESS DISTINCTNESS. weak-verdict-flip and weak-first-row-commits both sit on
#   single-row failing batches but at distinct values and for distinct reasons
#   (polarity inversion vs. an unconditional first-row commit). weak-rollback-all
#   is the only reject on a clean batch, where the other three coincide with the
#   frozen solution.
# WITNESS SUBJECT. Every reject case is refuted against `_LOOPFREE`, not against
#   gold, and the reason is recorded rather than assumed: gold's `while` fixpoint
#   elaborates through `Classical.choice`, so `decide` on the frozen tester is
#   stuck for every claim. Measured here — the real witness and its exact
#   opposite (`= true`) both failed on gold with the same `did not reduce to
#   `isTrue` or `isFalse``, so the frozen side's exit code carried no
#   information, and a forged witness asserting a rival CORRECT would have
#   cleared both halves. Against `_LOOPFREE` the same witnesses fail by actually
#   deciding the claim false, with the `= true` control deciding green, so each
#   rejection is attributable to the spec.
AXIOM_TESTS = []
