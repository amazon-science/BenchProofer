"""properties.py — G-PBT falsification battery for django__django-12965 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct directDeleteEligible``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a reference-count carrier):

  directDeleteEligible (mut tableRefs : List Nat) return (direct : Bool)
    ensures tableRefs = withTarget tableRefsOld          -- (C1) mut-frame
    ensures direct ↔ liveCount tableRefsOld.tail = 0     -- (C2) the decision

where a deletion query is modeled by the list of usage counts of the tables it
addresses (a table is "live" when its count is positive) with the TARGETED table
at the head, ``withTarget`` applies the deletion's own use of that targeted table
(its count goes up by one, no other count changes), and ``liveCount`` counts the
positively-counted entries. Two INDEPENDENT behaviours are pinned:

  * (C1) the ONLY state change is the deletion's own use of the table it targets
    — the post-state reference-count vector is EXACTLY ``withTarget`` of the entry
    vector, nothing else mutated. This is a ``mut``-frame clause (directive 5):
    it pins the exact post-state of the sole mutated binder, so a rival that
    leaves the vector at a different value is caught here regardless of what it
    returns.
  * (C2) the boolean answer is whether NO table other than the targeted one is
    live — ``liveCount tableRefsOld.tail = 0``. The clause is stated over the
    non-targeted tables alone, so it is insensitive to how many times the
    targeted table itself is used (including not at all).

The carrier is FULLY TRANSPARENT: ``withTarget`` / ``liveCount`` are transparent
``def``s over ``List Nat`` / ``Nat``, and the ``axioms`` region declares no
``axiom`` (``withTarget`` is a deep A-reference validated == the real callee by
axiom_check.py — that is G-AX's job — NOT a consumed answer key, so there is no
opaque oracle to echo, directive 8). So the whole reject lane is expressible by
``decide`` at concrete literal inputs; no witness binds a hypothesis and there is
no joint-satisfiability obligation.

BINDER STRUCTURE. The postcondition has ONE input binder — the entry value of
the ``mut`` parameter, ``tableRefs : List Nat`` (surfaced to the tester as
``tableRefsOld``). Both clauses read it: C1 pins the post-state to ``withTarget``
of it; C2 pins the answer to ``liveCount …tail = 0`` of it. The reject
witnesses drive it to FIVE distinct points — ``[]`` (no table recorded at all),
``[0]`` (a single unused table), ``[1]`` (the targeted table used once),
``[1, 1]`` (a second table also live), and ``[1, 0]`` (a second table present but
not live) — so the vector is varied in length (0, 1, 1, 2, 2) and in liveness
content, and both the targeted-table use and the no-other-live comparison are
probed off a single pinned shape (pts = 5).

The ``[1, 0]`` point is what makes ``liveCount``'s LIVENESS FILTER load-bearing.
At the other four points the post-state vector (``[1]``, ``[1]``, ``[2]``,
``[2, 1]``) has NO trailing zero entry, so over the tail ``liveCount`` and
``List.length`` cannot be told apart and a rival that counted every non-targeted
table rather than only the live ones would agree with the spec at all four.
``[1, 0]`` has tail ``[0]``, where ``liveCount = 0`` (direct) but ``length = 1``
(subquery), so the filter is the sole reason the two disagree — see
``count-all-not-live``.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches the postcondition through Velvet's own tester machinery:
``extract_program_for`` -> ``directDeleteEligibleExec``, then
``prove_precondition_decidable_for`` / ``prove_postcondition_decidable_for`` /
``derive_tester_for`` synthesize the ``Decidable`` instances and the boolean
tester ``directDeleteEligibleTester : List Nat → Bool`` (its one argument is the
``mut`` parameter at its ENTRY value). ``directDeleteEligibleTester xs = false``
says the extracted program's (post-state, returned-bool) pair violates C1 ∧ C2 at
entry vector ``xs``. It is checked in a file whose ``prove_correct`` block has
been stripped, so no tactic script can mask the verdict; there are no ``require``
clauses, so every input reaches the postcondition (nothing is vacuously
excluded); every equality is over decidable carriers, so no assumption
(``axiom`` / ``sorry`` / ``native_decide``) is needed and the ``example`` head
binds nothing (the consistency probe is trivially satisfied). Each reject witness
below was run against BOTH the rival (``decide`` proves the tester is ``false``,
so it elaborates, exit 0) and the frozen solution (``decide`` proves the tester
is ``true`` there, so the ``= false`` claim fails to build, exit 1) with two real
builds — the required discrimination.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION — NOT vacuous here, unlike most Lean/Velvet
    ports. The nagini sibling holds the query's read-only reference-count
    quantity under a fractional heap permission (``Acc(query.extra_active, ...)``)
    and its frame rival WRITES that quantity to satisfy the discriminator
    vacuously, rejected by nagini's frame postcondition ``extra_active ==
    Old(extra_active)``. That permission-enforced frame becomes, on this
    referentially-transparent backend, the genuine ``mut``-frame clause C1
    (``tableRefs = withTarget tableRefsOld``): the reference-count vector IS a
    ``mut`` binder, and a rival that leaves it at a wrong post-state violates C1
    exactly as the nagini write violated the frame clause. So this class PORTS
    (case ``frame-mut-write-vector``) rather than being written off — the
    directive-5 frame is the carrier analogue of nagini's permission frame.

  * DIVERGENCE / NON-TERMINATION - INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. NOT a spec hole; the earlier
    text in this slot said the opposite and every factual claim it made is
    retracted here.
    The frozen impl region is LOOP-FREE (straight-line ``let`` / ``if`` over
    immutable values, no loop and no recursion), so there is no control flow here
    to make diverge: a rival cannot obtain divergence by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it.
    The retraction. The earlier text said this bundle sets
    ``loom.semantics.termination "partial"`` (Solution.lean line 4), under which a
    non-terminating impl satisfies C1 ∧ C2 VACUOUSLY and VERIFIES, and recorded the
    class as a known hole with a corpus census of 401 admitting bundles. Line 4
    reads ``"total"``, and the file's only correctness ``open`` is
    ``open TotalCorrectness DemonicChoice``; the two cannot disagree, because the
    ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). The census had no referent
    either: all 500 velvet bundles set ``"total"`` and open
    ``TotalCorrectness``, so there is no ``partial`` cohort to belong to.
    What the semantics do. Under ``total`` a postcondition is claimed of ALL runs,
    not only terminating ones, and the verifier demands a decreasing measure on
    every loop. Measured on this bundle with the proof reduced to a bare
    ``loom_solve``: a spliced spun loop with no ``decreasing`` clause is refused at
    elaboration (``Decreasing annotations are required in total correctness
    semantics``), and the sharper shape that CARRIES a measure which does not
    decrease (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``
    with body ``q := q``) is REJECTED on the measure's own goal -
    ``case «decreasing_1: q»``, residual ``⊢ q < q``. So a never-answering rival
    does not satisfy this spec and there is no verify-does-not-imply-resolve break
    to record. The nagini sibling carries no ``diverge-*`` / ``nonterm-*`` case
    either, so nothing was dropped in the port.

  * UNGROUNDED-ORACLE ECHO — N/A. Both clauses are total relations of the input
    vector (via ``withTarget`` / ``liveCount`` / equality); the ``axioms`` region
    is empty, so there is no opaque answer key a wrong impl could echo. The
    cheapest correct impl does the bump-then-count honestly, which the
    positive controls cover.

  * THE CALLER (``delete_uses_subquery`` / ``as_sql``) IS UNMODELED. The nagini
    sibling additionally contracts the downstream caller that turns the predicate
    into a direct-vs-subquery emission, with its own postconditions (Q1/Q2/Q3),
    and attaches five rivals to it (``always-subquery``, ``always-direct``,
    ``partial-domain-dus-*``, ``frame-mut-dus-*``, ``pos/admiss-dus-*``). This
    bundle models only the purely-functional decision core (the single method
    ``directDeleteEligible``), so those caller-attached cases have NO counterpart
    here — carrier narrowing, not an omission gap. See the accounting footer for
    the case-by-case disposition.

ADMISSIBILITY lane: LIVE, not vacuous. The pre-conditions region declares no
``require``, but that does NOT make the lane degenerate: the total-carrier
analogue of PRECOND-TOO-STRONG is the obligation being unsatisfiable or
DEGENERATE at an F2P-shaped input, and ``admiss-accounting-nondegenerate``
discharges C2's decision at the point ``[]`` (empty tail, so no other table is
live and ``direct = true``) and at the contrasting point ``[1, 1]`` (tail
``[1]``, one live, so ``direct = false``) as an in-region ``assert``, by
evaluation, before closing
the frozen obligation verbatim. The assert is load-bearing: the same module under
the frozen bare ``loom_solve`` fails with an unsolved ``admiss_1`` goal.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; ``withTarget`` is
a deep A-reference validated == the real callee by axiom_check.py). The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-12965"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The whole `-- impl-start` / `-- impl-end` block lies
# ---- inside the region the spec view elides and occurs exactly once in
# ---- Solution.lean (both facts asserted at load by _swap), so a _swap on it
# ---- touches only the elided impl region and `same_spec` holds. ----
_IMPL = (
    "    -- impl-start\n"
    "    tableRefs := withTarget tableRefs\n"
    "    return liveCount tableRefs.tail == 0\n"
    "    -- impl-end"
)

# ---- the frozen proof body (everything under the `prove_correct` header),
# ---- unique in the file and elided from the spec view. The positive controls
# ---- verify under it verbatim (their reshapes close with the same bare
# ---- `loom_solve`); every reject rival keeps it too — its rejection is carried
# ---- by the machine-checked witness, not by whether the frozen script happens
# ---- to break on the reshape. ----
_PROOF = (
    "prove_correct directDeleteEligible by\n"
    "  loom_solve"
)


def _with_impl(body: str, proof: str = _PROOF) -> str:
    """Solution.lean with ONLY the impl block replaced (spec view untouched)."""
    m = _swap(_BASE, _IMPL,
              "    -- impl-start\n" + body + "\n    -- impl-end")
    if proof is not _PROOF:
        m = _swap(m, _PROOF, proof)
    return m


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery. `directDeleteEligibleTester xs = false` says the extracted
# ---- program's (post-state, returned-bool) pair violates C1 ∧ C2 at entry
# ---- vector `xs`. List Nat / Nat are DecidableEq, so `decide` settles it with
# ---- no assumption and no bound hypothesis.
_TESTER = (
    "extract_program_for directDeleteEligible\n"
    "prove_precondition_decidable_for directDeleteEligible\n"
    "prove_postcondition_decidable_for directDeleteEligible\n"
    "derive_tester_for directDeleteEligible\n\n"
)


def _witness(xs: str) -> str:
    return _TESTER + (
        "example : directDeleteEligibleTester " + xs + " = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the byte-identical
    # C1 / C2 obligation and only reshapes the executable surface; both verify
    # under the frozen `loom_solve` verbatim (checked out-of-band with real
    # builds).
    # =====================================================================
    {
        "id": "pos-control-answer-before-mutate",
        "kind": "soundness",
        "expect": "verify",
        # Reorder: compute the decision from `withTarget` of the ENTRY vector into
        # a local FIRST, then apply the usage-bump mutation, then return the local.
        # `withTarget` leaves the tail untouched, so the tail the frozen impl counts
        # after mutating is the same list, the returned bool is identical and the
        # post-state is still `withTarget tableRefsOld` — C1 and C2 both hold.
        "module": _with_impl(
            "    let d := liveCount tableRefs.tail == 0\n"
            "    tableRefs := withTarget tableRefs\n"
            "    return d"),
        "rationale": "structurally-different CORRECT reshape: read the decision "
                     "off the entry vector's non-targeted tables into a local before "
                     "applying the targeted-table mutation, then return the local. The "
                     "counted term is unchanged, so C2 (direct ↔ liveCount "
                     "tableRefsOld.tail = 0) holds, and the post-state is "
                     "still exactly `withTarget tableRefsOld`, so C1 holds. Verifies "
                     "under the frozen `loom_solve`. If a faithful reshape failed "
                     "to verify the spec would be over-fit to the mutate-then-count "
                     "statement order => SPEC-TOO-STRONG. Also the honest "
                     "no-ungrounded-echo control: the accounting-then-count IS the "
                     "work, not an echo of any oracle. (Sibling: "
                     "pos-control-rst-direct-discriminator.)",
    },
    {
        "id": "pos-control-decide-eq",
        "kind": "soundness",
        "expect": "verify",
        # Equivalent arithmetic form of the comparison: `decide (liveCount … = 0)`
        # for the Bool result instead of the `== 0` beq. Same value at every input,
        # so C2 still holds; the mutation is untouched, so C1 holds.
        "module": _with_impl(
            "    tableRefs := withTarget tableRefs\n"
            "    return decide (liveCount tableRefs.tail = 0)"),
        "rationale": "structurally-different CORRECT reshape: express the boolean "
                     "with `decide (liveCount tableRefs.tail = 0)` (propositional "
                     "equality) rather than the `== 0` boolean-equality operator. "
                     "The two agree at every input, so C2 (direct ↔ liveCount "
                     "tableRefsOld.tail = 0) still holds; the targeted-table "
                     "mutation is byte-identical, so C1 holds. Verifies under the "
                     "frozen `loom_solve`. A faithful reshape that could not verify "
                     "would mean the clause is over-fit to the `==` FORM => "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). Added by AUDIT: the port dropped
    # this lane claiming it was inexpressible because the pre-conditions region
    # declares no `require`. That reason is wrong — the analogue on a total
    # carrier is the obligation being NON-DEGENERATE at an F2P-shaped input,
    # which an in-region `assert` discharged by evaluation tests directly.
    # =====================================================================
    {
        "id": "admiss-accounting-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen impl verbatim, preceded by an in-region `assert` that
        # discharges C2's decision function at the F2P-shaped point BY
        # EVALUATION, and at a contrasting point, before the frozen obligation
        # is closed. The assert is a real proof obligation, not decoration: with
        # the frozen bare `loom_solve` this module FAILS with an unsolved
        # `admiss_1` goal (measured, exit 1), so the case only passes because the
        # three conjuncts are actually proven.
        "module": _with_impl(
            "    assert (with_name_prefix `admiss (\n"
            "      withTarget [] = [1] ∧\n"
            "      liveCount ([] : List Nat).tail = 0 ∧\n"
            "      liveCount [1, 1].tail = 1))\n"
            "    tableRefs := withTarget tableRefs\n"
            "    return liveCount tableRefs.tail == 0",
            "prove_correct directDeleteEligible by\n"
            "  loom_solve\n"
            "  all_goals decide"),
        "rationale": "ADMISSIBILITY / PRECOND-TOO-STRONG lane. The obligation is "
                     "satisfiable AND NON-DEGENERATE at both ends of the decision: "
                     "the entry vector `[]` (no table recorded) has an empty tail, "
                     "so no non-targeted table is live and C2 forces `direct = "
                     "true` THERE — that point is reachable and decided "
                     "affirmatively, not excluded — while `[1, 1]` has tail `[1]`, "
                     "one live non-targeted table, so C2 forces `direct = "
                     "false` there. Both conjuncts are discharged BY EVALUATION as "
                     "an in-region `assert`, before the frozen C1 ∧ C2 obligation "
                     "is closed with the impl verbatim. If the assert could not "
                     "discharge, the decision would be degenerate (constant over "
                     "the domain) or the F2P-shaped input unreachable => "
                     "PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE. The assert IS "
                     "load-bearing: under the frozen bare `loom_solve` this module "
                     "fails with an unsolved `admiss_1` goal, so `all_goals decide` "
                     "is what proves it — a variant may legitimately supply a "
                     "tactic body since only the STATEMENT is frozen. (Sibling: "
                     "admiss-caller-establishes-predicate-precond, re-aimed from "
                     "call-site precondition admissibility — which needs a modeled "
                     "caller and a `require` surface, neither of which exists here "
                     "— to post-image non-degeneracy at the F2P point, the shape "
                     "the sibling cells use. ADDED by audit.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument for why its faithful
    # real counterpart would NOT resolve the failing test
    # (F2P: test_fast_delete_all).
    # =====================================================================

    # ---- DROP-THE-FIX (C1 + C2): the exact pre-patch regression ----
    {
        "id": "drop-fix-no-accounting",
        "kind": "uniqueness",
        "expect": "reject",
        # THE reported regression: require the WHOLE vector to hold exactly one
        # live table, and skip the deletion's own use of the table it targets. On
        # the entry vector `[]` that count is 0 ≠ 1, so it returns the subquery
        # decision where the spec returns the direct decision; and the post-state
        # vector is left unmutated, violating the frame clause.
        "module": _with_impl(
            "    return liveCount tableRefs == 1"),
        "refinement": "this IS the regression the issue reports: a delete whose "
                      "query records no table usage at all counts zero live tables, "
                      "decides it is not confined to one table, and compiles to "
                      "the subquery form `... WHERE id IN (SELECT ...)`. The failing "
                      "test asserts the whole-table delete issues a single query "
                      "with no SELECT subquery, so this faithful counterpart FAILS "
                      "it and does NOT resolve.",
        "rationale": "REJECT from C1 AND C2: the rival leaves the post-state vector "
                     "unmutated (C1 demands `withTarget tableRefsOld`) and decides "
                     "off the whole vector rather than the non-targeted tables (C2 "
                     "demands `liveCount tableRefsOld.tail = 0`). Refuted at the "
                     "empty entry vector `[]` — where the tail is empty so no "
                     "non-targeted table is live and the spec gives `direct = true`, "
                     "but the rival leaves `tableRefs = []` "
                     "and returns `liveCount [] == 1 = false`. This is the ONE input "
                     "of length zero no other rival "
                     "probes. If it verified => SPEC-TOO-WEAK (admits the pre-patch "
                     "bug). (Sibling: drop-fix-no-primary-present.)",
        "witness": _witness("[]"),
    },

    # ---- FRAME / mut-frame (C1 only): the ported permission-mutation rival ----
    {
        "id": "frame-mut-write-vector",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame attack: compute the CORRECT decision (so C2 holds), but leave the
        # reference-count vector at a WRONG post-state (`[]`) instead of `withTarget`
        # of the entry vector. The nagini sibling writes the framed read-only
        # quantity to satisfy the discriminator vacuously and is rejected by the
        # frame postcondition; here the frame is the `mut` clause C1 and the wrong
        # post-state violates it directly. C2 is kept correct so the rejection is
        # attributable solely to the frame clause.
        "module": _with_impl(
            "    let d := liveCount tableRefs.tail == 0\n"
            "    tableRefs := []\n"
            "    return d"),
        "refinement": "this is the shape whose faithful counterpart returns the "
                      "right single-table decision but corrupts the query's "
                      "reference-count bookkeeping as a side effect (mutating it to "
                      "an empty/wrong state rather than performing exactly the "
                      "one targeted-table usage bump). Any later compilation step "
                      "that reads that reference-count state would then see a "
                      "corrupted vector and mis-compile subsequent deletes, "
                      "breaking the PASS_TO_PASS delete suite; so it does NOT "
                      "resolve. Correct on the returned decision at every input (a "
                      "pure frame break).",
        "rationale": "REJECT from C1 (tableRefs = withTarget tableRefsOld): the "
                     "rival overwrites the vector to `[]`, but C1 pins the "
                     "post-state to `withTarget tableRefsOld`, which is NEVER `[]` "
                     "(`withTarget` always yields a non-empty list). C2 still holds "
                     "(the returned bool is the correct decision), so the rejection "
                     "is attributable solely to the mut-frame clause. Refuted at the "
                     "entry vector `[1]` — where C1 demands `withTarget [1] = [2]` "
                     "but the rival leaves `[]` (and the decision `d = true` is "
                     "correct). This is the frame-mutation probe: the nagini "
                     "permission-frame rival re-expressed against the directive-5 "
                     "mut-frame. If it verified => SPEC-TOO-WEAK (the exact "
                     "post-state is unpinned). (Sibling: frame-mut-write-extra-active.)",
        "witness": _witness("[1]"),
    },

    # ---- PARTIAL-DOMAIN (C2): correct except on the boundary sub-domain ----
    {
        "id": "partial-domain-le-two",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct where the post-state has at most two live tables in total, but
        # WRONG once a second table is live alongside the targeted one: returns the
        # direct decision where the spec (no other table live) returns the subquery
        # decision. Drops only that boundary sub-domain.
        "module": _with_impl(
            "    tableRefs := withTarget tableRefs\n"
            "    return decide (liveCount tableRefs ≤ 2)"),
        "refinement": "a faithful counterpart tolerating up to two live tables "
                      "rather than requiring the delete be confined to the one it "
                      "targets would compile a delete that genuinely addresses a "
                      "second live table (one extra active join) to the direct "
                      "single-table form, dropping the join "
                      "filter and deleting the wrong rows — breaking the multi-table "
                      "PASS_TO_PASS delete tests. So it does NOT resolve. It stays "
                      "correct where only the targeted table is live, so it "
                      "would still pass the whole-table F2P — a genuine "
                      "partial-domain break the F2P alone would miss.",
        "rationale": "REJECT from C2 (direct ↔ liveCount tableRefsOld.tail = "
                     "0): with a second live table the spec's tail count is 1 ≠ 0 so "
                     "`direct = false`, but the post-state total is `2 ≤ 2` so the "
                     "rival returns true. Refuted at the "
                     "entry vector `[1, 1]` — post-state `[2, 1]`, tail `[1]` with "
                     "`liveCount = 1` — where the spec gives `direct = false` and the "
                     "rival gives true. This drives the vector to length two with two "
                     "live entries, the boundary sub-domain no other rival probes. If "
                     "it verified => SPEC-TOO-WEAK (the no-other-live requirement is "
                     "loosened). (Sibling: partial-domain-rst-le-one.)",
        "witness": _witness("[1, 1]"),
    },

    # ---- INVERTED (C2): the negated discriminator ----
    {
        "id": "predicate-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # The targeted-table usage bump is applied (so C1 holds), but the decision
        # is the NEGATION of the correct one: direct iff some OTHER table IS live.
        # Wrong on the whole domain except where both sides coincide.
        "module": _with_impl(
            "    tableRefs := withTarget tableRefs\n"
            "    return liveCount tableRefs.tail != 0"),
        "refinement": "an inverted decision (direct exactly when the delete is NOT "
                      "confined to the table it targets) would compile a whole-table "
                      "delete — which touches no other table — to the "
                      "subquery form, and a genuine multi-table delete to the direct "
                      "form: both wrong. It FAILS the whole-table F2P (which asserts "
                      "no SELECT subquery) and mis-compiles multi-table deletes, so "
                      "it does NOT resolve.",
        "rationale": "REJECT from C2 (direct ↔ liveCount tableRefsOld.tail = "
                     "0): the rival returns the negation of the pinned decision, so "
                     "it disagrees wherever a non-targeted table either is or is not "
                     "live. Refuted at the entry vector `[0]` — a single UNUSED "
                     "table, post-state `[1]` (`withTarget [0] = [1]`), empty tail "
                     "with `liveCount = 0` — where the spec gives `direct = true` but "
                     "the rival returns `false`. This drives the vector to a "
                     "length-one unused entry, exercising the usage bump on a zero "
                     "head that no other rival probes. If it verified => "
                     "SPEC-TOO-WEAK. (Sibling: predicate-inverted.)",
        "witness": _witness("[0]"),
    },

    # ---- LIVENESS FILTER (C2): count every addressed table, not just the live
    # ---- ones. Added by AUDIT — the four rivals above leave `liveCount`'s filter
    # ---- unattacked, because every input they use yields a post-state whose TAIL
    # ---- has no zero entry, where `liveCount` and `List.length` coincide.
    {
        "id": "count-all-not-live",
        "kind": "uniqueness",
        "expect": "reject",
        # The usage bump is applied (so C1 holds), but the count DROPS THE LIVENESS
        # FILTER: it counts every addressed table instead of only the
        # positively-counted ones. Agrees with the spec wherever the post-state tail
        # has no zero entry — including all four points the other rivals use — and
        # diverges exactly when a non-targeted table is present but not live.
        "module": _with_impl(
            "    tableRefs := withTarget tableRefs\n"
            "    return tableRefs.length == 1"),
        "refinement": "a faithful counterpart deciding single-table eligibility "
                      "from the NUMBER OF ADDRESSED TABLES rather than the number "
                      "of positively-referenced ones would compile a delete whose "
                      "extra table is addressed but no longer actively referenced "
                      "(its reference count already dropped to zero) to the "
                      "subquery form instead of the direct form. It still passes "
                      "the whole-table F2P (an empty state yields a "
                      "single-entry vector, where the two counts coincide), so this "
                      "is a break the F2P alone cannot see; it needlessly emits the "
                      "slow subquery for deletes the direct form handles, and the "
                      "dropped-reference states in the PASS_TO_PASS delete suite are "
                      "where it diverges. So it does NOT resolve.",
        "rationale": "REJECT from C2 (direct ↔ liveCount tableRefsOld.tail = "
                     "0): the rival counts list ENTRIES over the whole post-state "
                     "where C2 counts NON-ZERO entries among the non-targeted tables, "
                     "so it diverges whenever a non-targeted table is present but "
                     "dead. Refuted at the entry vector `[1, 0]` — tail `[0]`, where "
                     "`liveCount [0] = 0` so the spec gives "
                     "`direct = true`, but the rival returns `[2, 0].length == 1 = "
                     "false`. This is the ONLY shipped input whose post-state TAIL "
                     "contains a zero, so it is the only one at which the liveness "
                     "filter is load-bearing: at `[]`/`[0]`/`[1]`/`[1, 1]` the "
                     "post-state tails `[]`/`[]`/`[]`/`[1]` have no zero entry and "
                     "`liveCount` there equals `List.length`, so this rival AGREES "
                     "with the spec at all four and no other witness can see it. C1 "
                     "still holds (the usage-bump mutation is byte-identical), so "
                     "the rejection is attributable solely to C2's liveness filter. "
                     "If it verified => SPEC-TOO-WEAK (the `≠ 0` filter in "
                     "`liveCount` would be doing no work). (Sibling: none — this "
                     "distinction is carrier-specific: nagini models the same state "
                     "as a single extra-active COUNT, which cannot express an "
                     "addressed-but-dead table, so the sibling has no such rival to "
                     "port. ADDED by audit.)",
        "witness": _witness("[1, 0]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 11 SPEC cases (2
# soundness positives, 1 admissibility, 2 frame-mutation rivals, 6 uniqueness
# rivals) plus an EMPTY AXIOM lane (AXIOM_TESTS = []). The sibling contracts TWO
# functions: the changed predicate `references_single_table` (the single-alias
# decision, modeled HERE as `directDeleteEligible`) and its UNCHANGED downstream
# caller `delete_uses_subquery` (`as_sql`, which turns the predicate into a
# direct-vs-subquery emission). This velvet bundle models ONLY the
# purely-functional decision core — the single method `directDeleteEligible` with
# clauses C1 (mut-frame) / C2 (the decision) — so every sibling case attached to
# the caller has NO counterpart here (carrier narrowing, 433/500 velvet bundles
# carry exactly one `prove_correct` where the nagini sibling contracts five-plus
# functions). Chasing parity would mean fabricating rivals for an unmodeled
# function; do not.
#
#   sibling case (nagini)                    -> here                        disposition
#   ------------------------------------------------------------------------------------
#   pos-control-rst-direct-discriminator     -> pos-control-answer-before-mutate  PORTED
#   (no direct sibling)                       -> pos-control-decide-eq             ADDED
#   pos-control-dus-not-predicate            -> (none)                       UNMODELED (caller)
#   admiss-caller-establishes-predicate-precond -> admiss-accounting-nondegenerate
#                                                                            RE-AIMED (audit 2)
#   frame-mut-write-extra-active             -> frame-mut-write-vector       PORTED
#   frame-mut-dus-write-extra-active         -> (none)                       UNMODELED (caller)
#   partial-domain-rst-le-one                -> partial-domain-le-two        PORTED
#   partial-domain-dus-direct-on-extra-one   -> (none)                       UNMODELED (caller)
#   drop-fix-no-primary-present              -> drop-fix-no-accounting       PORTED
#   always-subquery                          -> (none)                       SUBSUMED (see below)
#   always-direct                            -> (none)                       SUBSUMED (see below)
#   predicate-inverted                       -> predicate-inverted           PORTED
#   (no sibling — carrier-specific)          -> count-all-not-live           ADDED (audit)
#   AXIOM_TESTS (none)                       -> (none)                       N/A (G-AX)
#
# 5 uniqueness (4 ported + 1 added by audit), 1 soundness ported + 1 added, 1
# admissibility RE-AIMED (audit 2); 3 caller-attached cases UNMODELED; 2
# caller-attached constant-answer cases SUBSUMED; axiom lane empty. = 8 SPEC
# cases (2 soundness, 1 admissibility, 5 uniqueness).
#
# ADMISSIBILITY (added by AUDIT 2 — the port's omission reason was FALSE). The
#   port recorded admiss-caller-establishes-predicate-precond as inexpressible on
#   two grounds: it is caller-attached, and "the pre-conditions region is empty so
#   there is no precondition surface that could be too strong". The second ground
#   is wrong, and it is the one that matters: on a TOTAL carrier the analogue of
#   PRECOND-TOO-STRONG is the obligation being unsatisfiable or DEGENERATE at an
#   F2P-shaped input, which an in-region `assert` discharged BY EVALUATION tests
#   directly — the shape used by 423 sibling velvet cells that likewise declare no
#   `require`. Measured, not argued: `assert (withTarget [] = [1] ∧ liveCount
#   ([] : List Nat).tail = 0 ∧ liveCount [1, 1].tail = 1)` ahead of the frozen
#   impl FAILS under the frozen bare `loom_solve` (exit 1, unsolved `admiss_1`
#   goal) and VERIFIES under `loom_solve; all_goals decide` (exit 0), as do three
#   other tactic spellings. So the assert is a real obligation and the lane is
#   live. Shipped as admiss-accounting-nondegenerate; without it this battery
#   tested only SPEC-TOO-WEAK and SPEC-TOO-STRONG, dropping one of the three
#   directions the gate exists to test (scripts/pbt_coverage.py flagged exactly
#   this).
#
# SUBSUMED, not inexpressible (corrected by AUDIT). The sibling's `always-subquery`
#   / `always-direct` are attached to the caller, but their CLASS — a constant
#   answer that ignores the state entirely — re-expresses directly on the decision
#   core as `return true` / `return false` after the usage bump, and the audit built
#   both: each is rejected by C2 and carries a discriminating witness (`return true`
#   refuted at `[1, 1]` and `[1, 1, 1]`, `return false` at `[0, 0]`; rival exit 0 /
#   gold exit 1 on real builds). They are NOT shipped because their discriminating
#   power is strictly SUBSUMED: a constant `true` is refuted at exactly the points
#   `partial-domain-le-two` already refutes (any state with ≥ 2 live tables) and a
#   constant `false` at exactly the points `predicate-inverted` already refutes (any
#   state whose non-targeted tables are all dead). Adding them would raise the case count
#   without adding a probed point. The port's stated reason ("no method to attach
#   them to") was wrong; the disposition (do not ship) is right for a different
#   reason, recorded here rather than left as a false inexpressibility claim.
#
# PORTED (soundness): pos-control-rst-direct-discriminator is a
#   structurally-different correct predicate impl (the sibling computes the
#   decision from the discriminator directly instead of via the count-helper). It
#   ports as pos-control-answer-before-mutate (read the decision off the entry
#   vector's non-targeted tables before applying the usage bump) — a genuine
#   control-flow reshape that keeps both clauses and verifies under the frozen
#   proof. A second positive (pos-control-decide-eq, an equivalent arithmetic form
#   of the comparison) is ADDED so the soundness surface is defended from two
#   distinct reshapes.
# PORTED (uniqueness, the `_rst`/predicate rivals): drop-fix-no-primary-present ->
#   drop-fix-no-accounting (drop the usage-bump step; the exact reported
#   regression; refuted at the empty whole-table vector, violating C1 AND C2).
#   frame-mut-write-extra-active -> frame-mut-write-vector (the sibling's
#   permission-frame rival: write the framed quantity to satisfy the discriminator
#   vacuously; here the frame is the directive-5 mut-frame clause C1 and the wrong
#   post-state violates it while C2 is kept correct; refuted at `[1]`).
#   partial-domain-rst-le-one -> partial-domain-le-two (loosen the no-other-live
#   bound to ≤ 2; correct on the whole-table case, wrong at two live tables;
#   refuted at `[1, 1]`). predicate-inverted -> predicate-inverted (negate the
#   decision; refuted at `[0]`, a single dead table). Each carries a
#   machine-checked witness that ELABORATES against the rival and FAILS against the
#   frozen solution (two real builds per case).
# ADDED by AUDIT (uniqueness): count-all-not-live — count the addressed tables
#   rather than the LIVE ones (`tableRefs.length == 1` in place of `liveCount
#   tableRefs.tail == 0`), refuted at `[1, 0]`. The four ported rivals all drive the
#   binder to inputs whose ACCOUNTED vector is entirely live (`[1]`, `[2]`, `[1]`,
#   `[2, 1]`), where `liveCount` is extensionally `List.length`; so before this case
#   the `≠ 0` liveness filter in C2 — half the modeled predicate — was unattacked,
#   and a rival that dropped it agreed with all four shipped witnesses. It has no
#   nagini sibling because the sibling's carrier is a single extra-active COUNT,
#   which cannot represent an addressed-but-dead table; the distinction is one this
#   `List Nat` carrier ADDS rather than collapses.
# UNMODELED (3 caller-attached cases + 1 admissibility): pos-control-dus-not-
#   predicate, frame-mut-dus-write-extra-active and
#   partial-domain-dus-direct-on-extra-one are attached to the nagini caller
#   `delete_uses_subquery` (`as_sql`), which this bundle does not model — the velvet
#   twin contracts only the decision core `directDeleteEligible`. There is no method
#   to attach them to and no obligation for them to attack: each is a claim about
#   the direct-vs-subquery EMISSION, which is downstream of the boolean this bundle
#   defends, so re-expressing them would require modeling a function outside this
#   bundle's carrier. Genuine carrier narrowing, NOT an effort gap. (The
#   admissibility case is NOT among these — see the ADMISSIBILITY entry below; a
#   second audit found it expressible and landed it.) The two remaining sibling cases
#   (always-subquery / always-direct) are SUBSUMED, not unmodeled — see above.
# FRAME-MUTATION note: unlike most Lean/Velvet ports, this class is NOT vacuous
#   here. On a read-only input it would be (referential transparency, no heap).
#   But the reference-count vector is a `mut` binder pinned by C1
#   (`tableRefs = withTarget tableRefsOld`, directive 5), which is the exact
#   carrier analogue of nagini's permission-enforced frame `extra_active ==
#   Old(extra_active)`. So the sibling's `_rst` frame rival PORTS (frame-mut-write-
#   vector); the `_dus` frame rival is UNMODELED only because its host function is.
# DIVERGENCE: the nagini sibling ships NO divergence rival for this instance, so
#   there is nothing to port. Recorded for completeness, and CORRECTED: the class is
#   INAPPLICABLE to this loop-free impl and CLOSED BY THE SEMANTICS against any
#   rival that brings a loop of its own. It is NOT a spec hole.
#   The prior version of this note said the bundle uses
#   `loom.semantics.termination "partial"`, so a diverging impl satisfies every
#   `ensures` VACUOUSLY and VERIFIES, and called that a KNOWN SPEC HOLE with a
#   census of 401 admitting bundles. Line 4 reads "total", the only correctness
#   `open` in the file is `open TotalCorrectness DemonicChoice`, and the two cannot
#   disagree because the `set_option` elaborator itself runs
#   `openScope `TotalCorrectness` (Loom/MonadAlgebras/WP/Options.lean:169-186).
#   All 500 velvet bundles now read "total", so the cited cohort does not exist.
#   Under "total" a postcondition is claimed of ALL runs and every loop must carry a
#   decreasing measure. Measured on this bundle: an unmeasured spun loop is refused
#   at elaboration (`Decreasing annotations are required in total correctness
#   semantics`), and a loop carrying a NON-decreasing measure (`while q > 0 ...
#   decreasing q`, body `q := q`) is rejected on the measure's own goal --
#   `case «decreasing_1: q»`, residual `q < q`. Nothing is papered over and nothing
#   is escalated.
#
# BINDER / CLAUSE COVERAGE. The postcondition has ONE input binder — the entry
#   value of the `mut` parameter `tableRefs : List Nat` (surfaced as
#   `tableRefsOld`) — and TWO independent top-level clauses: C1 (the mut-frame
#   `tableRefs = withTarget tableRefsOld`) and C2 (the decision `direct ↔
#   liveCount tableRefsOld.tail = 0`). The five reject witnesses probe
#   five DISTINCT input points (pts=5):
#     * drop-fix-no-accounting     []      (attacks C1 AND C2; length 0, the edge)
#     * frame-mut-write-vector     [1]     (attacks C1 only; length 1, one live)
#     * partial-domain-le-two      [1, 1]  (attacks C2 only; length 2, two live)
#     * predicate-inverted         [0]     (attacks C2 only; length 1, one unused)
#     * count-all-not-live         [1, 0]  (attacks C2's liveness filter; length 2,
#                                          mixed — the ONLY point whose post-state
#                                          TAIL carries a dead entry)
#   So the single binder ranges over length {0, 1, 1, 2, 2} and liveness content
#   {empty, one-live, one-unused, two-live, live-plus-dead} — the usage bump
#   is exercised on an empty vector (`withTarget [] = [1]`), a live head
#   (`[1] -> [2]`), and a zero head (`[0] -> [1]`, the bump-a-zero-head case), and
#   the no-other-live test is probed on tails `[]` (drop-fix, frame, inverted),
#   `[1]` (partial) and `[0]` (count-all).
#   BOTH clauses are attacked: C1 by frame-mut-write-vector (cleanly, C2 held
#   correct) and drop-fix-no-accounting; C2 by predicate-inverted,
#   partial-domain-le-two, count-all-not-live and drop-fix-no-accounting. Within C2
#   BOTH sub-parts are attacked: the no-other-live COMPARISON (partial-domain-le-two,
#   predicate-inverted) and the LIVENESS FILTER that defines the count
#   (count-all-not-live) — the four ported rivals all sit at post-state tails with
#   no zero entry, where the filter is extensionally invisible, so it took the added
#   case to make it load-bearing. No two rivals are refuted at the same input; no clause
#   is left undefended (the two positives defend the whole obligation) or unattacked.
#
# WHAT THE AUDIT MEASURED, beyond the shipped cases. Correct reshapes that must NOT
#   be rejected: inlining `liveCount`'s filter body at the call site, and an
#   `if … then true else false` ladder over the count, both VERIFY (the first needs
#   `simp [liveCount]` after `loom_solve`, which a variant may legitimately supply —
#   only the STATEMENT is frozen, the tactic body is not). So the spec is not
#   over-fit to the `liveCount`/`==` spelling. Notably a whole-post-state
#   `decide (liveCount … ≤ 1)` also verifies, and CORRECTLY so: `withTarget` always
#   yields a non-empty list with a positive head, so on the post-state the total
#   live count is `1 + liveCount tail`, and `≤ 1` is extensionally
#   `liveCount tail = 0` on the reachable domain. That is exactly why the sibling's
#   `le-one` rival could not port as-is and had to be re-aimed to `le-two` — a
#   carrier collapse the port navigated correctly. Tuned WRONG impls that must be
#   rejected and were: prepending a fresh count instead of bumping the head (C1+C2),
#   counting the whole vector instead of the tail (C2), and both constant answers
#   (C2). None verified => no
#   SPEC-TOO-WEAK hole found in the reachable-input lane.
#
# AXIOM_TESTS: empty. The bundle declares no consumed axiom (mapping.md §3:
#   `withTarget` is a deep A-reference validated == the real callee by G-AX /
#   axiom_check.py, not a consumed `ensures`); the sibling's AXIOM_TESTS is
#   likewise empty. This gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
