"""properties.py — G-PBT falsification battery for django__django-13028 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against a
correct impl of the same spec — here the ``witness_reference``, for the reason
set out under WITNESS MECHANICS below).

DEFENDED SURFACE (one contracted method over a flattened node-sequence carrier,
``List Node``). The method reports whether a traversal over the visited operand
tree offends:

  filterClauseRejected (nodes : List Node) return (raised : Bool)
    ensures raised = anyBad nodes            -- THE load-bearing clause

``anyBad`` is a fully unfolded ``def`` in the ``pure`` region — there is NO
opaque answer key to echo. Its shape is a disjunction over the per-node
predicate ``nodeBad``:

  * ``anyBad []      = false``
  * ``anyBad (n::ns) = nodeBad n || anyBad ns``

and the per-node predicate is itself a CONJUNCTION over two independent node
flags:

  * ``nodeBad n = n.isOperand && !n.filterable``

So the single ``ensures`` clause folds two independent behaviours over the one
input binder ``nodes``: (a) the per-node CONJUNCTION — a node offends only when
it is BOTH a query operand AND declares itself non-filterable, so neither flag
alone triggers a report — and (b) the traversal DISJUNCTION — the whole report
is the OR over every visited node, so a report is owed exactly when SOME node
offends and none when every node is clean. Both must be exercised, and the reject
witnesses below vary ``nodes`` across BOTH node flags (``isOperand`` and
``filterable``) and across list length / position (first vs last vs sole element),
so no flag or position is left pinned at one value.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS here. The nagini sibling carries this class as
    MANDATORY because its inputs hold a fractional heap permission an impl can
    illegally overwrite (write the read-only carrier so the postcondition holds
    vacuously). Lean and Velvet are referentially transparent: ``nodes`` is an
    immutable value, there is no ``mut`` binder for it in this bundle, no heap
    and no aliasing — so there is no read-only input to mutate and no substitute
    probe to build. Not fabricated (per the porting map, this class is vacuous on
    Lean/Velvet).
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class: the post-image is a total,
    fully unfolded function of the method's own input (``anyBad`` and its helper
    ``nodeBad`` are concrete ``def``s in the ``pure`` region; the ``axioms``
    region is empty), so there is no answer key to echo. The nagini sibling notes
    the same and attacks the discriminating conjunction directly; those attacks
    port as reject rivals here.
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival correct on part of the input domain
    but diverging on a sub-domain — dropping one conjunct of the per-node guard,
    widening it to a disjunction, or skipping a position in the traversal.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``filterClauseRejectedTester nodes = false`` says the extracted program's result
violates the method's postcondition at that concrete input. It is checked in a
file whose ``prove_correct`` block has been stripped, so no tactic script can
mask the verdict. Each reject rival is written as a straight-line COMPUTABLE form
whose extracted program reduces, so its witness ELABORATES against the rival.

The SECOND half — the witness must FAIL against a correct impl — cannot use the
frozen solution here, and this is the load-bearing subtlety of this cell. The
frozen impl computes the report with a ``while`` loop; under
``loom.semantics.choice "demonic"`` that loop's fixpoint elaborates through
``Classical.choice``, which the kernel cannot unfold. Measured with real builds:
against the frozen solution EVERY one of these witnesses fails with

  ``its `Decidable` instance ... did not reduce to `isTrue` or `isFalse` ``

i.e. the kernel never evaluated the claim. A failure by stuck reduction is
evidence of nothing — the identical error appears for a TRUE claim about that
impl — so the frozen-side exit code discriminates nothing and a forged witness
asserting the rival is CORRECT would clear both halves. That is the
``witness-undecided`` defect, and it is NOT repairable by leaning on the
battery's own positives: both ``expect="verify"`` cases below retain the frozen
``while`` loop, and both were measured STUCK on these same witnesses too.

So every reject case names a ``witness_reference``: ``_LOOPFREE``, a loop-free
impl of the SAME frozen spec (``return anyBad nodes``) which shares the spec
byte-for-byte, VERIFIES, and — being loop-free — actually REDUCES. Measured:
each of the four witnesses fails against it with ``decide` proved that the
proposition ... is false`` — a real refutation, not a stuck reduction. The
reference is also shipped as an ``expect="verify"`` case (``pos-loopfree-direct``)
so the battery itself records that loop-freeness is a CORRECT shape and is not
what any rival is being rejected for.

WITNESS PLACEMENT. The four reject witnesses probe four DISTINCT input points
(``pts=4``), varying both node flags and the traversal position:
  * ``[{filterable:=false, isOperand:=false}]`` — a clean plain value (NOT an
    operand): the spec owes no report; refutes the drop-operand-conjunct rival,
    which reports on the false filterability flag alone. Isolates ``isOperand``;
  * ``[{filterable:=true, isOperand:=true}]`` — a PERMITTED operand: the spec owes
    no report; refutes the widen-to-OR rival, which reports on any operand.
    Isolates ``filterable``, a point the drop-operand rival CLEARS (so the two
    over-reporting rivals do not share a witness — each is separated at the flag
    it actually mishandles);
  * a two-node list with the offender FIRST — refutes the skip-first rival;
  * a two-node list with the offender LAST — refutes the skip-last rival. Mirror
    of the previous point, so neither positional rival pins the offender's index.
Each of the four was confirmed by two real builds to elaborate against its rival
and to be REFUTED (not merely stuck) against the reference.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the transformation is
modeled DEEPLY as ``nodeBad``/``anyBad``). There is no axiom-soundness /
axiom-containment obligation to probe here, and the gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13028"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single impl region and
# ---- is unique in Solution.lean (both facts asserted at load by _swap). ----

# The whole frozen impl body (loop + invariants). Replacing it with a
# straight-line computable form lets a rival's extracted program reduce under
# `decide` so its witness can discriminate.
_IMPL = (
    "    let mut result : Bool := false\n"
    "    let mut i := nodes.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ nodes.length\n"
    "      invariant result = anyBad (nodes.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let n := nodes[i - 1]!\n"
    "      result := nodeBad n || result\n"
    "      i := i - 1\n"
    "    return result\n"
)

# The single fold-step assignment inside the loop body (unique in the file: the
# other `nodeBad`/`anyBad` occurrences are in the pure region and lemmas).
_FOLD = "      result := nodeBad n || result\n"

# The first line of the impl body — an anchor to PREPEND an in-region assert
# before, keeping the frozen body intact after it.
_IMPL_HEAD = "    let mut result : Bool := false\n"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives), so a variant may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. The body below is the frozen script, unique in the file. ----
_PROOF = (
    "prove_correct filterClauseRejected by\n"
    "  loom_solve\n"
    "  rw [anyBad_drop_step nodes i (by omega) (by omega)]\n"
    "  simp_all\n"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with the WHOLE impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_fold(new_fold: str, new_proof: str) -> str:
    """Reshape only the fold-step assignment AND retune the frozen tactic script."""
    return _swap(_swap(_BASE, _FOLD, new_fold), _PROOF, new_proof)


def _with_assert(assert_block: str, new_proof: str) -> str:
    """Prepend an in-region assert before the frozen body AND retune the script."""
    return _swap(_swap(_BASE, _IMPL_HEAD, assert_block + _IMPL_HEAD), _PROOF, new_proof)


# ---- the witness REFERENCE. The frozen impl's `while` loop elaborates through
# ---- `Classical.choice` under demonic choice, so `decide` against it is stuck
# ---- for EVERY claim and its exit code discriminates nothing. This loop-free
# ---- impl of the SAME spec shares the frozen spec, VERIFIES, and REDUCES, so it
# ---- is the subject each witness is refuted against instead. The whole battery
# ---- shares this one reference and the gate verifies it once. It is also shipped
# ---- as an expect="verify" case below, so the battery records that loop-freeness
# ---- is a correct shape rather than the reason any rival is rejected. ----
_LOOPFREE = _swap(
    _swap(_BASE, _IMPL, "    return anyBad nodes\n"),
    _PROOF,
    "prove_correct filterClauseRejected by\n  loom_solve\n")


# ---- witness preamble. Reaches the method's postcondition through Velvet's own
# ---- tester machinery. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. This method has no
# ---- `require` clause, so every probed input is admissible and the tester
# ---- reaches the postcondition rather than vacuously passing. ----
_TESTER = (
    "extract_program_for filterClauseRejected\n"
    "prove_precondition_decidable_for filterClauseRejected\n"
    "prove_postcondition_decidable_for filterClauseRejected\n"
    "derive_tester_for filterClauseRejected\n\n"
)


def _wit(nodes_lit: str) -> str:
    return _TESTER + (
        f"example : filterClauseRejectedTester {nodes_lit} = false := by\n  decide\n")


# Concrete node literals (both flags spelled out at every point).
_CLEAN_PLAIN = "[{ filterable := false, isOperand := false }]"        # not an operand
_OFFENDER = "{ filterable := false, isOperand := true }"             # operand, non-filterable
_CLEAN_OPERAND = "{ filterable := true, isOperand := true }"         # operand, filterable
_PERMITTED_EXPR = "[{ filterable := true, isOperand := true }]"      # single permitted operand


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. The fold accumulates the SAME disjunction with
    # its two operands COMMUTED (`result || nodeBad n`); the accumulated value
    # is unchanged, so the byte-identical obligation still holds. The frozen
    # tactic script gains a single `Bool.or_comm` rewrite to reconcile the
    # reordered `||`.
    # =====================================================================
    {
        "id": "pos-commute-fold-or",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_fold(
            "      result := result || nodeBad n\n",
            "prove_correct filterClauseRejected by\n"
            "  loom_solve\n"
            "  rw [anyBad_drop_step nodes i (by omega) (by omega)]\n"
            "  simp_all [Bool.or_comm]\n"),
        "rationale": "commuting the two operands of the fold-step disjunction "
                     "(`result || nodeBad n` for `nodeBad n || result`) leaves the "
                     "accumulated value identical, so the loop invariant "
                     "`result = anyBad (nodes.drop i)` and hence "
                     "`raised = anyBad nodes` still hold; a correct reshape MUST "
                     "verify, else SPEC-TOO-STRONG on operand order.",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — the loop-free direct form, which is ALSO
    # the `witness_reference` every reject case below is refuted against. It
    # replaces the backward fold with the pure function the postcondition names
    # (`return anyBad nodes`), which is a structurally different but CORRECT
    # impl: it drops the loop and its invariants entirely, so `loom_solve` alone
    # closes the obligation. Shipping it as a case is what makes the reference
    # honest — the battery records on its own that loop-freeness VERIFIES, so no
    # reader can suspect a rival was rejected merely for being loop-free (every
    # rival below is loop-free too).
    # =====================================================================
    {
        "id": "pos-loopfree-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _LOOPFREE,
        "rationale": "returning `anyBad nodes` directly is the extensionally "
                     "identical straight-line form of the frozen backward fold: "
                     "the postcondition `raised = anyBad nodes` becomes an "
                     "immediate `rfl`-shaped goal, so `loom_solve` closes it with "
                     "no invariant reasoning. A correct reshape MUST verify, else "
                     "SPEC-TOO-STRONG on the choice of traversal shape. This case "
                     "also certifies the `witness_reference` the reject cases use: "
                     "it shares the frozen spec, it verifies, and (being loop-free) "
                     "its extracted program REDUCES, which the frozen loop's does "
                     "not.",
    },

    # =====================================================================
    # ADMISSIBILITY — this method carries no `require` clause, so the usual
    # "a normal input satisfies the precondition" probe is vacuous: nothing
    # could exclude an F2P-shaped input. The residual admissibility risk on a
    # total domain is that the post-image is DEGENERATE at the interesting
    # points — a spec no impl can meet reads exactly like a spec every impl
    # meets. So this case discharges an in-region `assert` at two F2P-shaped
    # points: a single clean plain value (not an operand) for which the report
    # must be FALSE, and a single offending operand for which the report must be
    # TRUE. The verifier must establish the post-image really does demand a
    # non-degenerate report on each. The frozen body follows the assert, so the
    # method's own `ensures` obligation still discharges; the assert is live, not
    # decoration (a false claim about the same points leaves an unsolved goal —
    # verified out-of-band).
    # =====================================================================
    {
        "id": "admiss-report-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_assert(
            "    assert (with_name_prefix `admiss\n"
            "      (anyBad [{ filterable := false, isOperand := false }] = false ∧\n"
            "       anyBad [{ filterable := false, isOperand := true }]  = true))\n",
            "prove_correct filterClauseRejected by\n"
            "  loom_solve\n"
            "  all_goals\n"
            "    first\n"
            "    | exact ⟨rfl, rfl⟩\n"
            "    | (rw [anyBad_drop_step nodes i (by omega) (by omega)]; simp_all)\n"),
        "rationale": "the post-image is non-degenerate at the F2P-shaped points: a "
                     "single clean plain value (not an operand) must report FALSE "
                     "and a single offending operand (non-filterable operand) must "
                     "report TRUE — not the constant-false or constant-true a "
                     "degenerate/unsatisfiable obligation would admit. The in-region "
                     "assert must discharge (else the obligation is degenerate at "
                     "the interesting points); the frozen body keeps "
                     "`raised = anyBad nodes` intact, so the module verifies.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line COMPUTABLE impl (so its witness
    # reduces under `decide`) refuted at a concrete input by a witness that fails
    # on the frozen loop-solution, and each with the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "prepatch-drop-operand-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch guard: report on `!filterable` alone, dropping the
        # is-operand conjunct — reports on a plain value that merely carries a
        # false filterability flag.
        "module": _with_impl("    return nodes.any (fun n => !n.filterable)\n"),
        "refinement": "this is the pre-patch guard — it reports purely on a false "
                      "filterability flag, without first checking the value is a "
                      "query operand. A plain comparison value that happens to "
                      "carry a false filterability flag then triggers the report, "
                      "which is exactly the spurious rejection the issue describes "
                      "and the failing test pins (a plain value with that flag must "
                      "be accepted). A faithful counterpart that dropped the "
                      "is-operand conjunct would NOT resolve.",
        "rationale": "REJECT from `raised = anyBad nodes`: `anyBad` clears a node "
                     "that is not an operand (the per-node conjunction requires "
                     "BOTH flags), and this impl reports on it whenever its "
                     "filterability flag is false. Refuted at a single clean plain "
                     "value (not an operand, non-filterable), where the spec owes "
                     "FALSE and the rival reports TRUE — the `isOperand` binder.",
        "witness": _wit(_CLEAN_PLAIN),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "widen-conjunction-to-or",
        "kind": "uniqueness",
        "expect": "reject",
        # Widen the per-node guard from AND to OR: report on `isOperand OR
        # !filterable`. Over-reports on BOTH a clean plain non-filterable value
        # AND a permitted (filterable) operand.
        "module": _with_impl(
            "    return nodes.any (fun n => n.isOperand || !n.filterable)\n"),
        "refinement": "widening the per-node guard to a disjunction reports on "
                      "EVERY query operand (even a permitted, filterable one) and "
                      "on every non-filterable plain value — so both a legitimate "
                      "filterable-operand filter and a plain value with a false "
                      "filterability flag are rejected, breaking the queries that "
                      "must be accepted. A faithful counterpart using OR would NOT "
                      "resolve.",
        "rationale": "REJECT from `raised = anyBad nodes`: the per-node predicate "
                     "is a CONJUNCTION, so a permitted operand (operand, "
                     "filterable) is cleared, yet the disjunctive rival reports on "
                     "it. Refuted at a single permitted operand, where the spec owes "
                     "FALSE and the rival reports TRUE — the `filterable` binder, a "
                     "point the drop-operand rival (which clears that node) does "
                     "not share.",
        "witness": _wit(_PERMITTED_EXPR),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "partial-domain-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Skip the FIRST visited node: report over `nodes.drop 1`. A disallowed
        # operand appearing first is never seen and the report is missed.
        "module": _with_impl("    return (nodes.drop 1).any nodeBad\n"),
        "refinement": "screening only the tail of the traversal and skipping the "
                      "first visited node lets a disallowed query expression "
                      "supplied at the head through without a report — diverging "
                      "from gold on the disallowed-expression rejection the failing "
                      "expression test relies on. A faithful counterpart that "
                      "skipped the first visited node would NOT resolve.",
        "rationale": "REJECT from `raised = anyBad nodes`: `anyBad` ORs over EVERY "
                     "node including the head, and this impl drops the head. "
                     "Refuted at a two-node list whose OFFENDER is first and whose "
                     "tail is clean, where the spec owes TRUE and the rival reports "
                     "FALSE — varies list length and the head position.",
        "witness": _wit(f"[{_OFFENDER}, {_CLEAN_OPERAND}]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "partial-domain-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Skip the LAST visited node: report over `nodes.dropLast`. A disallowed
        # operand appearing last is never seen and the report is missed.
        "module": _with_impl("    return nodes.dropLast.any nodeBad\n"),
        "refinement": "an off-by-one that stops one node short of the end skips the "
                      "last visited operand, so a disallowed query expression "
                      "appearing last in the traversal is missed and accepted — "
                      "diverging from gold on disallowed-expression rejection for "
                      "trees whose offender is last. A faithful counterpart with "
                      "that off-by-one would NOT resolve.",
        "rationale": "REJECT from `raised = anyBad nodes`: `anyBad` ORs over EVERY "
                     "node including the last, and this impl drops the last. "
                     "Refuted at a two-node list whose OFFENDER is last and whose "
                     "head is clean, where the spec owes TRUE and the rival reports "
                     "FALSE — the last position, the MIRROR of the skip-first "
                     "point, so neither rival pins the offender's position.",
        "witness": _wit(f"[{_CLEAN_OPERAND}, {_OFFENDER}]"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals — one of which is a frame-
# mutation probe). This bundle models the SAME single behaviour (the per-node
# filterability guard folded over the visited operand tree), so every sibling
# case except the frame probe has a counterpart here.
#
#   sibling case                     -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder-conjuncts    -> pos-commute-fold-or               PORTED
#   admiss-bool-local                -> admiss-report-nondegenerate       PORTED
#   frame-mutation-write-is_expr     -> (none)                            VACUOUS
#   prepatch-drop-is_expr-conjunct   -> prepatch-drop-operand-conjunct    PORTED
#   widen-conjunction-to-or          -> widen-conjunction-to-or           PORTED
#   partial-domain-skip-first        -> partial-domain-skip-first         PORTED
#   partial-domain-skip-last         -> partial-domain-skip-last          PORTED
#   (no sibling)                     -> pos-loopfree-direct               ADDED
#
# 6 ported, 1 vacuous = 7, plus 1 backend-specific positive added.
#
# ADDED (pos-loopfree-direct): no nagini counterpart — it exists because of a
#   VELVET carrier fact the nagini sibling cannot have. The frozen impl's `while`
#   loop elaborates through `Classical.choice` under demonic choice, so `decide`
#   against the frozen tester is stuck for every claim and the frozen side cannot
#   serve as the witness's second subject (`witness-undecided`). This loop-free
#   impl of the same spec is the `witness_reference` all four rivals are refuted
#   against; shipping it as an expect="verify" case is what certifies that
#   loop-freeness VERIFIES and is therefore not the property any rival is being
#   rejected for. Measured: gold and BOTH loop-retaining positives are stuck on
#   these witnesses; the reference verifies and refutes all four.
#
# DIVERGENCE / NON-TERMINATION lane - the class is CLOSED BY THE SEMANTICS
#   here, and a diverging rival is REJECTED rather than admitted. This bundle
#   sets ``loom.semantics.termination "total"`` AND carries
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
#
# PORTED (positive control): the sibling reorders the two conjuncts of the
#   per-node guard (`permitted[i]==0 and is_expr[i]==1`). The carrier here folds
#   a DISJUNCTION over the traversal, so the analogous structural reshape is
#   commuting the fold-step disjunction (`result || nodeBad n`). The ARGUMENT is
#   identical — a correct-but-different shape must verify — and it survives the
#   frozen script with one `Bool.or_comm` rewrite. Verified to build.
# PORTED (admissibility): the sibling's bool-local reshape self-establishes that
#   a normal F2P-shaped input reaches the accepting path. This bundle has no
#   `require` clause, so the precondition-admits probe is vacuous; the live
#   residual risk on a total domain is a degenerate post-image. Expressed as an
#   in-region assert that the report is non-degenerate at two F2P-shaped points
#   (a clean plain value -> FALSE; an offending operand -> TRUE). The assert is
#   live (a false claim leaves an unsolved goal — verified out-of-band); the
#   frozen body keeps the ensures obligation intact. Verified to build.
# VACUOUS (frame-mutation): the sibling carries this as MANDATORY because its
#   inputs hold a fractional heap permission (Acc(...,1/2)) an impl can illegally
#   overwrite. This backend is referentially transparent and this bundle declares
#   no `mut` binder for `nodes`, so it is an immutable value with no heap
#   footprint — there is no read-only input to overwrite and no substitute probe
#   to build. Not fabricated (per the porting map: this class is vacuous on
#   Lean/Velvet).
# PORTED (the four value rivals): the sibling's prepatch-drop-conjunct,
#   widen-to-OR, skip-first and skip-last rivals port directly onto the single
#   `raised = anyBad nodes` clause. Each is a straight-line computable impl whose
#   extracted program reduces under `decide` (the frozen loop-solution stays
#   stuck), and each carries a machine-checked witness that ELABORATES against the
#   rival and FAILS against the frozen solution (verified with two real builds per
#   case). The four witnesses probe `nodes` at four distinct points that vary BOTH
#   node flags and the traversal position: a clean plain value (isOperand=false),
#   a permitted operand (filterable=true), an offender-first list and an
#   offender-last list — so both the per-node conjunction (both flags) and the
#   traversal disjunction (head/last position) are exercised. drop-operand and
#   widen both over-report but are separated by the flag they mishandle
#   (isOperand vs filterable), so each has its own distinguishing witness;
#   skip-first and skip-last are refuted at mirror positions so neither pins the
#   offender's index.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the transformation is modeled deeply as nodeBad/anyBad), so there is
# nothing to probe.
AXIOM_TESTS = []
