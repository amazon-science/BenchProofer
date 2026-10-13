"""properties.py — G-PBT falsification battery for django__django-15930 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method assembling a single conditional branch
from an already-compiled CONDITION fragment and an already-compiled CONSEQUENT
fragment, each a text + ordered bound-parameter pair (``Compiled``):

  assembleConditionalBranch (cond : Compiled) (res : Compiled)
    ensures cond.sql ≠ [] → out = branchClause cond res
    ensures cond.sql = []  → out = branchClause truePredicate res

Both inputs are FREE, read-only values (neither ``mut``); there is no ``require``
clause, so the admitted domain is total. The carrier is fully transparent
(``Compiled`` derives ``DecidableEq``; ``truePredicate`` and ``branchClause`` are
concrete ``def``s, the ``axioms`` region declares nothing), so every witness
decides at concrete literals — no opaque term forces conditioning.

The postcondition is two INDEPENDENT guarded clauses over one derived branch:
  C1 (non-empty condition): the branch splices the supplied condition fragment
     verbatim — its text between the keywords and its parameters ahead of the
     consequent's (``branchClause`` fixes both the template splice and the
     parameter order cond.params ++ res.params).
  C2 (empty condition): the load-bearing correction — an empty condition text
     would leave no predicate between the keywords, so the branch must instead
     splice a NON-EMPTY always-true predicate (``truePredicate``: text and
     parameters both taken from it), never the empty fragment.

ADVERSARIAL READ of the nagini classes (sibling contracts one function,
``render_branch`` / ``When.as_sql``, over four read-only fragment inputs; this
bundle models the same assembly step as one method over (cond, res)):
  * FRAME-MUTATION (sibling's mandatory class) — VACUOUS here. It exists on
    nagini because an input carries a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: every parameter is
    an immutable value (neither ``cond`` nor ``res`` is ``mut``), there is no
    heap and no aliasing, so there is no read-only input to mutate and no
    substitute probe to build. Reported vacuous, not fabricated (footer).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully-unfolded
    function of the method's own two arguments (``truePredicate``/
    ``branchClause`` are concrete) — there is no opaque answer key to echo.
    Instead an honest cheapest-reshape POSITIVE CONTROL defends the obligation.
  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals right on part of the domain but
    diverging on a sub-domain: the empty-condition substitution dropped (C2), the
    parameter concatenation order reversed (C1 params half), the condition slot
    text sourced from the wrong fragment (C1 text half). Each is refuted at a
    concrete point; the witnesses vary both input fragments across the
    empty/non-empty and distinct-content boundaries.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the always-true
predicate is modeled DEEPLY as concrete data, validated == the real callee by
axiom_check.py / G-AX as an A-reference, not consumed here). The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15930"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl region (everything the variants replace). Two contiguous
# ---- lines wholly inside the one `-- impl-start` / `-- impl-end` region and
# ---- unique in Solution.lean (the `let effCond` line occurs nowhere else);
# ---- both facts are asserted at load by _swap. --------------------------------
_GOLD_IMPL = (
    "    let effCond : Compiled := if cond.sql = [] then truePredicate else cond\n"
    "    return branchClause effCond res"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# The frozen proof body (the `prove_correct` tactic script). Elided from the
# consumer spec view, so a variant that adds an in-region `assert` (which raises
# an extra side goal `loom_solve` leaves open) may retune it to discharge that
# goal — the obligation STATEMENT and the `prove_correct` header are untouched,
# so same_spec still holds. Anchored on the exact frozen script.
_GOLD_PROOF = "prove_correct assembleConditionalBranch by\n  loom_solve"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_proof(body, proof):
    """Reshape the impl block AND retune the `prove_correct` tactic body."""
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _GOLD_PROOF, proof)


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery:
# ---- `assembleConditionalBranchTester cond res = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. `Compiled` derives DecidableEq, so
# ---- the postcondition is decidable and every witness closes by `decide`.
def _tester(pre=""):
    m = "assembleConditionalBranch"
    return (f"{pre}extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify; else the post-image is SPEC-TOO-STRONG. Branch
    # order flipped: test the NON-EMPTY condition first and swap the two
    # bodies. Observationally identical on every input (the selected fragment
    # is truePredicate iff the condition text is empty, either way), and the
    # single point-wise equality needs no new lemma, so the frozen `loom_solve`
    # still discharges it. Verified in /tmp.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let effCond : Compiled := if cond.sql ≠ [] then cond else truePredicate\n"
            "    return branchClause effCond res"),
        "rationale": "a correct reshape (guard flipped to test the non-empty "
                     "condition first, bodies swapped) selects the identical "
                     "fragment on every input and adds no new proof obligation, "
                     "so both guarded equality clauses still discharge under the "
                     "frozen `loom_solve`; a rejection would be SPEC-TOO-STRONG "
                     "on impl shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous. Re-aimed (as the velvet
    # exemplar does) at the residual risk on a total domain: that the post-image
    # is UNSATISFIABLE / degenerate at the decisive corner — the empty-condition
    # case C2, where the correction lives. This discharges an in-region `assert`
    # pinning the assembled branch for the empty condition to the NON-EMPTY
    # always-true splice (text `WHEN %s THEN R`, parameters `[1, 5]`), i.e. the
    # empty fragment is NOT what appears between the keywords. The impl is kept
    # verbatim so the method's own obligation still discharges; the assert is
    # live (a false claim about the same point leaves an unsolved goal), so the
    # retuned proof `loom_solve <;> decide` is honest, not a weakening. Verified.
    # =====================================================================
    {
        "id": "admiss-empty-substitutes-nonempty",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      (branchClause truePredicate "
            "({ sql := \"R\".toList, params := [5] } : Compiled)\n"
            "        = { sql := \"WHEN %s THEN R\".toList, params := [1, 5] }))\n"
            + _GOLD_IMPL,
            "prove_correct assembleConditionalBranch by\n  loom_solve <;> decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "empty-condition corner (C2): the assembled branch splices "
                     "the NON-EMPTY always-true predicate (text `WHEN %s THEN R`, "
                     "params `[1, 5]`), so an empty condition never yields a "
                     "predicate-less branch. The in-region assert must discharge "
                     "(else the obligation is unsatisfiable / PRECOND-TOO-STRONG); "
                     "the impl is verbatim so both equality clauses still "
                     "discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Witnesses vary BOTH fragment
    # binders across the empty/non-empty and distinct-content boundaries; the
    # two independent guarded clauses (C1 text, C1 params, C2 substitution) are
    # each attacked.
    # =====================================================================
    {
        "id": "weak-prepatch-no-substitution",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix behaviour. Splices the supplied condition fragment
        # UNCONDITIONALLY, with no empty-condition substitution. Correct on
        # every non-empty condition (C1); wrong exactly on the empty-condition
        # sub-domain (C2), where the empty text is spliced between the keywords
        # and the always-true parameter is dropped.
        "module": _impl("    return branchClause cond res"),
        "refinement": "the faithful real counterpart is the pre-patch assembly: "
                      "it splices the compiled condition straight in with no "
                      "empty-condition guard. A match-everything filter compiles "
                      "to an empty fragment, so the assembled branch has no "
                      "predicate between the keywords — a syntax error at "
                      "execution. The failing test that annotates every row via "
                      "such a filter still raises. It would NOT resolve.",
        "rationale": "REJECT from C2 (`cond.sql = [] → out = branchClause "
                     "truePredicate res`): at an empty condition the post-image "
                     "demands the always-true splice (text `WHEN %s THEN ...`, "
                     "params `[1] ++ res.params`) but the impl emits the empty "
                     "splice (text `WHEN  THEN ...`, params `res.params`). "
                     "Refuted at `cond = {[],[]}`, `res = {\"X\",[]}`.",
        "witness": _tester() +
                   "example : assembleConditionalBranchTester "
                   "{ sql := [], params := [] } "
                   "{ sql := \"X\".toList, params := [] } = false := by\n  decide\n",
    },
    {
        "id": "weak-params-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Renders the correct TEXT (and applies the empty-condition
        # substitution), but concatenates the bound parameters in the WRONG
        # order: consequent's ahead of the condition's, rather than the
        # condition's first. Isolates the parameter half of C1; the text half
        # and C2's text still hold.
        "module": _impl(
            "    let effCond : Compiled := if cond.sql = [] then truePredicate else cond\n"
            "    return { sql := (branchClause effCond res).sql, "
            "params := res.params ++ effCond.params }"),
        "refinement": "binding the consequent's parameters ahead of the "
                      "condition's places every placeholder in the wrong "
                      "position, so the branch compares/returns the wrong values "
                      "whenever either fragment binds a parameter. The row-value "
                      "assertions in the annotate/update/filter tests that carry "
                      "bound parameters still fail. It would NOT resolve.",
        "rationale": "REJECT from the parameter half of C1 (`branchClause` fixes "
                     "params = cond.params ++ res.params): with `cond` binding "
                     "`[7]` and `res` binding `[9]` the post-image demands "
                     "`[7, 9]` but the impl emits `[9, 7]`. Text (both C1 and C2) "
                     "still holds, isolating the ordering. Refuted at "
                     "`cond = {\"A\",[7]}`, `res = {\"B\",[9]}` — a NON-EMPTY "
                     "condition, the C1 sub-domain.",
        "witness": _tester() +
                   "example : assembleConditionalBranchTester "
                   "{ sql := \"A\".toList, params := [7] } "
                   "{ sql := \"B\".toList, params := [9] } = false := by\n  decide\n",
    },
    {
        "id": "weak-condition-slot-from-consequent",
        "kind": "uniqueness",
        "expect": "reject",
        # On the non-empty branch, fills the condition SLOT TEXT from the
        # consequent fragment `res` instead of the supplied condition (params
        # kept in the correct order). Correct params, wrong condition text:
        # isolates the text half of C1 independently of the parameter rival.
        "module": _impl(
            "    let effCond : Compiled := if cond.sql = [] then truePredicate else cond\n"
            "    return { sql := \"WHEN \".toList ++ res.sql ++ \" THEN \".toList "
            "++ res.sql, params := effCond.params ++ res.params }"),
        "refinement": "placing the consequent's text in the condition slot "
                      "renders `WHEN <result> THEN <result>` — the branch "
                      "predicate is the wrong expression on every non-trivial "
                      "condition, so the bulk of the annotate/filter/update tests "
                      "that assert row selection by the intended predicate still "
                      "fail. It would NOT resolve.",
        "rationale": "REJECT from the text half of C1 (`branchClause` splices "
                     "cond.sql between the keywords): with `cond` text `C` and "
                     "`res` text `D` the post-image demands `WHEN C THEN D` but "
                     "the impl emits `WHEN D THEN D`. Parameters (order correct) "
                     "still hold, isolating the condition-slot text. Refuted at "
                     "`cond = {\"C\",[3]}`, `res = {\"D\",[8]}` — a NON-EMPTY "
                     "condition distinct from the parameter rival's input.",
        "witness": _tester() +
                   "example : assembleConditionalBranchTester "
                   "{ sql := \"C\".toList, params := [3] } "
                   "{ sql := \"D\".toList, params := [8] } = false := by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation, 3 partial-domain rivals). The
# sibling contracts `render_branch` over FOUR read-only fragment inputs
# (pred, pred_params, cons, cons_params) with a three-clause postcondition
# P1 (text) / P2 (params) / P3 (slot-non-blank length). This bundle models the
# same assembly step as one method over (cond, res : Compiled), each a text +
# params pair, with two guarded clauses C1 (non-empty condition) and C2 (empty
# condition = the always-true substitution). The sibling's empty-vs-non-empty
# predicate branch IS this bundle's C2-vs-C1 split.
#
#   sibling case                         -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder            -> pos-branch-reorder            PORTED
#   admiss-gold                           -> admiss-empty-substitutes-nonempty RE-AIMED
#   partial-domain-prepatch (P1+P3, empty)-> weak-prepatch-no-substitution PORTED
#   partial-domain-params-order (P2)      -> weak-params-order-reversed    PORTED
#   partial-domain-nonempty-slot (P1)     -> weak-condition-slot-from-consequent PORTED
#   frame-mutate-cons-params              -> (none)                        VACUOUS
#   frame-mutate-pred                     -> (none)                        VACUOUS
#
# 4 ported, 1 re-aimed, 2 vacuous = 7.
#
# RE-AIMED (admissibility): the sibling's case is the unmodified gold impl,
#   attesting the four Acc(...,1/2) preconditions ADMIT an F2P-shaped input. No
#   method here has a `require` clause, so that reading is vacuous; the case is
#   re-aimed (per the velvet exemplar) at proving the post-image is satisfiable
#   and NON-degenerate at the decisive empty-condition corner (C2), via an
#   in-region assert discharged symbolically against concrete literals.
# FRAME-MUTATION (both sibling cases): VACUOUS here. The sibling rivals WRITE a
#   read-only input held at Acc(...,1/2) (list.append needing full permission).
#   This backend is referentially transparent, has no heap and no aliasing, and
#   this bundle declares NO `mut` binder — there is no read-only input to
#   overwrite and no substitute probe to build. No case fabricated. P3
#   (slot-non-blank length) has no independent counterpart either: it is the
#   nagini device that makes the empty-slot violation observable; here the
#   text-level clause C2 pins the non-empty always-true splice directly (the
#   assembled text is `WHEN %s THEN ...`, structurally non-empty between the
#   keywords), so weak-prepatch-no-substitution attacks it as part of C2 and no
#   separate length rival is meaningful.
#
# BINDER / POINT COVERAGE. The three reject witnesses probe three distinct
# inputs across both clauses and both binders:
#   (cond={[],[]},   res={"X",[]})   weak-prepatch-no-substitution   [C2]
#   (cond={"A",[7]}, res={"B",[9]})  weak-params-order-reversed      [C1 params]
#   (cond={"C",[3]}, res={"D",[8]})  weak-condition-slot-from-consequent [C1 text]
# so cond.sql is varied over empty / "A" / "C", cond.params over [] / [7] / [3],
# res.sql over "X" / "B" / "D", res.params over [] / [9] / [8]. Neither fragment
# is pinned across the battery, both guarded clauses are attacked, and C1 is
# split into its text and parameter halves by two rivals refuted at DISTINCT
# non-empty inputs (so neither near-misses the other: the params rival renders
# correct text, the slot rival renders correct params).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the always-true predicate
# is a deep-model A-reference (concrete data validated == the real callee by
# axiom_check.py), not a consumed axiom, so there is nothing here to probe.
AXIOM_TESTS = []
