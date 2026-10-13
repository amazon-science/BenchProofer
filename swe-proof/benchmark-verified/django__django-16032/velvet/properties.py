"""properties.py — G-PBT falsification battery for django__django-16032 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct narrowRhsSubquery`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted decision over a four-observation carrier).
A membership subquery on the right-hand side of an ``__in`` test must be reduced
to a single output column exactly when it has not already been given a definite
output-column selection:

  narrowRhsSubquery (q : RhsQuery) return (narrow : Bool)
    ensures narrow = narrowsToSingleColumn q        -- and narrowsToSingleColumn
                                                    -- q = ! q.explicitlyProjected

The postcondition is a SINGLE top-level clause, and after unfolding the pure
definition it is exactly ``narrow = ! q.explicitlyProjected``. The whole point of
the change is *which* piece of the query's column state that decision reads. The
carrier ``RhsQuery`` carries FOUR observed booleans:

  * ``explicitlyProjected``      — the caller explicitly chose the output columns
                                   (an explicit projection was applied). This is
                                   the ONLY field the clause depends on.
  * ``hasExplicitSelectColumns`` — the query already carries an explicit list of
                                   select columns.
  * ``carriesAnnotations``       — the query carries annotation columns.
  * ``carriesExtraSelections``   — the query carries extra raw select columns.

There is NO opaque answer key to echo (directive 8): the ``axioms`` region is
empty, ``narrowsToSingleColumn`` is a concrete pure ``def``, and the post-image
is a total boolean function of the carrier. Pinning ``narrow =
! q.explicitlyProjected`` is grounded in the actual input, not an oracle.

The strength claim the battery must defend is TWO-SIDED and, crucially,
INDEPENDENCE-typed:
  (D1) not-designated => narrow   (explicitlyProjected false => narrow true),
  (D2) designated     => not-narrow (explicitlyProjected true  => narrow false),
  (I)  the decision is INDEPENDENT of the other three fields, in BOTH
       directions. Carrying an explicit-select list, annotation columns, or
       extra-select columns does NOT, on its own, designate the output columns
       (so it cannot suppress narrowing); and neither can any of them CANCEL a
       designation the caller did establish by explicitly projecting (so it
       cannot force narrowing either). Those three fields exist on the carrier
       precisely because a fragile pre-change heuristic consulted them; the
       fix's durability guarantee is that the decision no longer does, and a
       coupling of either sign is a failure of that guarantee.

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling
contracts THREE MUTATING operations on a minimal ``Query`` twin —
``project_columns`` (the explicit-projection state update), ``attach_auxiliary_
expressions`` (the annotate/alias state update, carrying THE reported bug in its
frame clause), and ``prepare_in_rhs`` (the guarded rhs-narrowing routine, with a
projection call, a pk-target guard, and value-grounded column clauses). Each
nagini case attaches to one of those mutations: a returned column list, a
cleared/preserved auxiliary-expression structure, a flag side effect, a specific
narrowed-to column value, or a permission/value frame.

THIS bundle models only the purely-functional core the fix actually turns on:
the narrowing DECISION itself — the guard ``not <the stored has-fields flag>``
that decides whether the rhs subquery is reduced to one column — as a pure
boolean function of the query's column-state booleans (mapping.md §1). It does
NOT model the mutations those operations perform: there is no returned column
list, no cleared auxiliary structure, no flag write, no narrowed-to column
value, and no ``mut`` state at all. The decision's four inputs are FREE booleans;
the SQL-compilation machinery the decision gates is unchanged code the decision
only triggers, never reshapes (mapping.md §3).

Consequently every nagini rival keyed on a mutation's VALUE FOOTPRINT — the
returned-column-list clauses, the auxiliary-structure clearing/frame clauses, the
narrowed-to-column value clause, the pk-target guard on the narrowing routine —
has NO counterpart on this carrier: none of those observations exists here. What
DOES survive is the narrowing decision's dependence on the query's column state,
and that is exactly what THE reported bug lived in — the pre-change derived
property judged an annotate()+alias() subquery to already designate its columns,
so narrowing was skipped and the sub-select returned N columns. That bug is the
``recouples`` rival below, and it is precisely this bundle's ``Solution_prepatch``.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. Lean and Velvet are referentially
    transparent: no heap, no aliasing, no fractional permission. ``q`` is an
    immutable value declared without ``mut``; there is no read-only field to
    overwrite and no permission level to abuse. The nagini value-frame rivals
    (``faith-aux-preserved-in-project``, ``frame-cols-in-aux``) attack a frame
    over the auxiliary-expression structure and the SELECT column list — neither
    is a modeled observation here (the mutations are unmodeled). No substitute
    probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. The ``axioms`` region is empty and
    ``narrowsToSingleColumn`` is a concrete ``def`` over the input; there is no
    answer key to echo.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
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

WITNESS PLACEMENT. Each reject rival is refuted at a concrete ``RhsQuery`` chosen
so the nine points together move each of the four fields across
``{false, true}`` and pin the decision's independence from the three decoy
fields in BOTH directions:
  * ``recouples``      at (P=F, S=F, A=T, E=F)  — isolates the annotation field;
  * ``couples-select`` at (P=F, S=T, A=F, E=F)  — isolates the select field;
  * ``couples-extra``  at (P=F, S=F, A=F, E=T)  — isolates the extra-select field;
  * ``always-narrow``  at (P=T, S=F, A=F, E=F)  — the (D2) direction;
  * ``never-narrow``   at (P=F, S=F, A=F, E=F)  — the (D1) direction;
and the mirror half of (I), where a decoy must not CANCEL a designation:
  * ``annot-overrides-projection``  at (P=T, S=F, A=T, E=F);
  * ``select-overrides-projection`` at (P=T, S=T, A=F, E=F);
  * ``extra-overrides-projection``  at (P=T, S=F, A=F, E=T);
and the JOINT half of (I), where no CONJUNCTION of decoys may cancel one:
  * ``compound-decoy-veto``         at (P=T, S=F, A=T, E=T).
Nine DISTINCT input points; no two rivals share one. The three
``*-overrides-projection`` rivals pair ``explicitlyProjected=true`` with each
decoy field in turn — the sub-domain the first five leave unwitnessed — and
``compound-decoy-veto`` is the only rival refuted at a point where TWO decoys are
set at once, which is the region every single-decoy rival agrees with the frozen
decision on. Each witness reaches the
``method`` contract through Velvet's own tester machinery
(``narrowRhsSubqueryTester q = false`` says the extracted program's result
violates the postcondition at that input) and is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. There are no ``require`` clauses, so every input reaches the
postcondition and ``decide`` settles it at a concrete record. Each witness was
verified out-of-band with two real builds: it ELABORATES against the rival and
FAILS against the frozen solution.

AXIOM lane: EMPTY (the bundle declares no ``axiom``; the decision is modeled
directly, not delegated to an oracle). The gate ignores ``AXIOM_TESTS``
regardless. Nagini->velvet accounting is at the bottom of the file.
"""
from pathlib import Path

INSTANCE = "django__django-16032"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The two executable lines of the frozen impl; they lie
# ---- wholly inside the single `-- impl-start`/`-- impl-end` region and appear
# ---- exactly once in Solution.lean (both facts asserted at load by _swap). ----
_IMPL = ("    let designated := q.explicitlyProjected\n"
         "    return !designated")


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched).

    Positive reshapes keep the frozen `prove_correct narrowRhsSubquery by
    loom_solve` script verbatim (verified out-of-band with real builds); each
    reject rival is judged by its witness, not by whether the frozen script
    happens to break on the reshaped impl.
    """
    return _swap(_BASE, _IMPL, new_impl)


# ---- frozen tactic body. `variant_scope` permits the `prove_correct` body to
# ---- differ (only the STATEMENT is frozen), which the admissibility case needs
# ---- in order to clear the extra in-region `assert` goal. ----
_PROOF = "prove_correct narrowRhsSubquery by\n  loom_solve"


def _with_impl_reproved(new_impl: str, new_proof: str) -> str:
    """Impl body replaced AND the (elided) tactic body retuned."""
    return _swap(_with_impl(new_impl), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery. RhsQuery is a
# ---- concrete four-Bool record, so `decide` settles the postcondition at a
# ---- concrete input. ----
_TESTER = (
    "extract_program_for narrowRhsSubquery\n"
    "prove_precondition_decidable_for narrowRhsSubquery\n"
    "prove_postcondition_decidable_for narrowRhsSubquery\n"
    "derive_tester_for narrowRhsSubquery\n\n"
)


def _rq(projected, select, annotations, extra):
    b = lambda x: "true" if x else "false"
    return ("{ explicitlyProjected := %s, hasExplicitSelectColumns := %s, "
            "carriesAnnotations := %s, carriesExtraSelections := %s }"
            % (b(projected), b(select), b(annotations), b(extra)))


def _witness(q_literal: str) -> str:
    return _TESTER + f"example : narrowRhsSubqueryTester {q_literal} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. The post-image is a point-wise boolean function
    # of the carrier, so no induction is needed and each reshape stays within
    # the frozen `loom_solve` script (each returns a value definitionally equal
    # to `! q.explicitlyProjected`). Both were verified with a real build.
    # =====================================================================
    {
        "id": "pos-spec-fn",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: return the pure spec function directly instead of inlining
        # the field read + negation. Same value; the frozen proof still closes.
        "module": _with_impl("    return narrowsToSingleColumn q"),
        "rationale": (
            "returning the pure decision function `narrowsToSingleColumn q` is "
            "definitionally `! q.explicitlyProjected`, so the single clause "
            "`narrow = narrowsToSingleColumn q` discharges; a structurally "
            "different but correct reshape must verify. If it fails => "
            "SPEC-TOO-STRONG (over-fit to the inlined field-read spelling)."
        ),
    },
    {
        "id": "pos-ite-form",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: express the decision as an explicit if/then/else branch on the
        # projection field rather than a boolean negation. Same value flow; the
        # frozen `loom_solve` script closes the byte-identical obligation.
        "module": _with_impl(
            "    return (if q.explicitlyProjected then false else true)"),
        "rationale": (
            "the branch `if q.explicitlyProjected then false else true` computes "
            "exactly `! q.explicitlyProjected`, so the clause holds; a "
            "control-flow reshape of the same decision must verify. If it fails "
            "=> SPEC-TOO-STRONG (the spec would be pinned to the negation "
            "spelling, not the decision)."
        ),
    },

    {
        # Added by the G-PBT audit. Both positives above are single-expression
        # reshapes that `loom_solve` closes by computation alone, so neither
        # shows the spec tolerates an impl that INSPECTS a decoy field. This one
        # branches on a decoy and returns the correct value on both arms: it is
        # observably the frozen decision, but only after a case split the frozen
        # script must perform. Confirmed to verify with a real build under the
        # byte-identical frozen `loom_solve` script.
        "id": "pos-decoy-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            "    if q.carriesAnnotations then\n"
            "      return !q.explicitlyProjected\n"
            "    else\n"
            "      return !q.explicitlyProjected"),
        "rationale": (
            "a correct impl is free to LOOK at a decoy field as long as its "
            "returned decision does not depend on it: both arms return "
            "`! q.explicitlyProjected`, so the clause "
            "`narrow = narrowsToSingleColumn q` holds on both branches and the "
            "impl is observably the frozen decision. This pins that the spec "
            "constrains the decision's VALUE, not which fields the impl may read "
            "— the independence claim (I) is about the post-image, not about "
            "syntactic field access. If it failed => SPEC-TOO-STRONG (the spec "
            "would forbid a faithful impl merely for touching a decoy field, and "
            "the three couples-* rivals would then be rejected for reading a "
            "field rather than for deciding wrongly)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY (added by the second G-PBT audit). The first audit dropped
    # this lane as "vacuous because the pre-conditions region is empty". That
    # reason is wrong, and it removes one of the three directions this gate
    # exists to test. On a TOTAL carrier the analogue of PRECOND-TOO-STRONG is
    # not an unsatisfiable `require` — it is the OBLIGATION being unsatisfiable,
    # or degenerately satisfiable, at exactly an F2P-shaped input. A positive
    # that discharges the obligation at that concrete input BY EVALUATION, as an
    # in-region `assert`, before closing the frozen obligation verbatim, tests
    # that directly.
    #
    # The assert is LIVE, not a restatement of the spec. Its two conjuncts pin
    # the decision's VALUE at two concrete inputs, and the second conjunct is
    # what makes it bite: a degenerate post-image (one satisfiable by a constant
    # decision, which is what `always-narrow`/`never-narrow` would exploit) would
    # fail one of the two halves. Confirmed live with a real build: flipping the
    # second conjunct's polarity does NOT verify (`decide` proved the proposition
    # false), so a wrong claim here is caught rather than waved through.
    # =====================================================================
    {
        "id": "admiss-f2p-decision",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      ((narrowsToSingleColumn " + _rq(False, False, True, False)
            + " = true) ∧\n"
            "       (narrowsToSingleColumn " + _rq(True, False, True, False)
            + " = false)))\n"
            + _IMPL,
            _PROOF + "\n  all_goals decide"),
        "rationale": (
            "the obligation is SATISFIABLE, and non-degenerately so, at an "
            "F2P-shaped input: a membership subquery that carries annotation "
            "columns and was never explicitly projected, i.e. "
            "(P=F, S=F, A=T, E=F). The in-region assert evaluates the decision "
            "there and pins it to `true` (it MUST be reduced to one column), and "
            "— the half that makes the probe bite — pins it to `false` at the "
            "same annotation-carrying query once the caller HAS explicitly "
            "projected it, (P=T, S=F, A=T, E=F). So the obligation is neither "
            "unsatisfiable at the failing-scenario input (PRECOND-TOO-STRONG on "
            "a total carrier) nor a constant collapse that any decision "
            "whatsoever would satisfy: the two points force opposite values, so "
            "no constant impl could discharge both. The impl is kept byte-verbatim "
            "so the method's own `ensures` still discharges; only the elided "
            "tactic body is retuned, and only to clear the extra assert goal "
            "(`variant_scope` freezes the obligation STATEMENT, not its script)."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing behaviour. The three "coupling"
    # rivals collectively pin independence (I): each isolates dependence on one
    # of the three decoy fields, mirroring the three disjuncts of the pre-change
    # derived heuristic. always/never pin the two directions (D1)/(D2).
    # =====================================================================
    {
        # THE reported bug, verbatim: the pre-change derived heuristic judged the
        # query to already designate its output columns from a disjunction of
        # (explicit-select list) OR (annotation columns) OR (extra selections),
        # so an annotate()+alias() rhs (annotation columns, no explicit
        # projection) was wrongly judged designated and narrowing was skipped.
        # This is exactly Solution_prepatch's skeleton.
        "id": "recouples",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let designated :=\n"
            "      q.hasExplicitSelectColumns || q.carriesAnnotations || q.carriesExtraSelections\n"
            "    return !designated"),
        "refinement": (
            "this is the pre-change derived heuristic verbatim — the decision "
            "reads a disjunction over the query's select-list / annotation / "
            "extra-selection state instead of the explicit-projection flag. Its "
            "faithful real counterpart is the unpatched code (the empty diff that "
            "keeps the derived property). A subquery built with annotate() then "
            "alias() carries annotation columns but was never explicitly "
            "projected, so the heuristic reports it as already designating its "
            "columns and the narrowing is skipped; the sub-select then returns "
            "many columns and the __in comparison raises "
            "'sub-select returns N columns - expected 1'. The F2P subquery test "
            "asserts the queryset resolves, so it would NOT resolve. This is the "
            "exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from the single clause `narrow = ! q.explicitlyProjected`: at "
            "(explicitlyProjected=F, annotations=T, others F) the spec requires "
            "narrow=true (not explicitly projected), but the rival's disjunction "
            "sees the annotation field and returns false. Refuted at "
            "(F,F,T,F) — isolating the ANNOTATION field, the exact bug's input. "
            "If it verified => SPEC-TOO-WEAK (the reported bug would go "
            "unnoticed)."
        ),
        "witness": _witness(_rq(False, False, True, False)),
    },
    {
        # Independence rival: re-couple the decision to the explicit-select-list
        # field (the FIRST disjunct of the pre-change heuristic) in isolation.
        # Correct exactly when that field agrees with explicit projection; wrong
        # when a query carries a select list but was not explicitly projected.
        "id": "couples-select",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let designated := q.explicitlyProjected || q.hasExplicitSelectColumns\n"
            "    return !designated"),
        "refinement": (
            "this reintroduces one disjunct of the pre-change fragile heuristic — "
            "the decision peeks at whether the query carries an explicit "
            "select-column list, in addition to the projection flag. The durable "
            "fix deliberately stopped consulting ANY internal column-state mask "
            "(the maintainer chose a stored flag set only by explicit projection "
            "over peeking into internals) precisely because such peeking is "
            "fragile. A query that carries a select-column list populated by a "
            "path other than explicit projection is judged by this rival to "
            "already designate its columns, so narrowing is skipped when it "
            "should fire — the same class of regression the durable fix "
            "eliminates. A faithful patch retaining this disjunct is an "
            "incomplete port of the fix that leaves that fragility in place."
        ),
        "rationale": (
            "REJECT from `narrow = ! q.explicitlyProjected`: at "
            "(explicitlyProjected=F, hasExplicitSelectColumns=T, others F) the "
            "spec requires narrow=true, but the rival returns false. Refuted at "
            "(F,T,F,F) — isolating the SELECT-LIST field, showing the decision "
            "must be INDEPENDENT of it. If it verified => SPEC-TOO-WEAK (the spec "
            "would not pin independence from the select-list field)."
        ),
        "witness": _witness(_rq(False, True, False, False)),
    },
    {
        # Independence rival: re-couple the decision to the extra-select-mask
        # field (the THIRD disjunct of the pre-change heuristic) in isolation.
        "id": "couples-extra",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let designated := q.explicitlyProjected || q.carriesExtraSelections\n"
            "    return !designated"),
        "refinement": (
            "this reintroduces the extra-raw-select disjunct of the pre-change "
            "fragile heuristic — the decision peeks at whether the query carries "
            "extra raw-select columns. As with the select-list disjunct, the "
            "durable fix stopped consulting this mask entirely; a query that "
            "carries extra selections but was not explicitly projected is judged "
            "by this rival to already designate its columns and narrowing is "
            "skipped when it should fire. A faithful patch keeping this disjunct "
            "leaves the same peek-into-internals fragility the fix removes, so it "
            "is an incomplete port of the fix rather than the durable "
            "flag-based decision."
        ),
        "rationale": (
            "REJECT from `narrow = ! q.explicitlyProjected`: at "
            "(explicitlyProjected=F, carriesExtraSelections=T, others F) the spec "
            "requires narrow=true, but the rival returns false. Refuted at "
            "(F,F,F,T) — isolating the EXTRA-SELECT field, showing the decision "
            "must be INDEPENDENT of it. A distinct input point and distinct "
            "decoy field from couples-select. If it verified => SPEC-TOO-WEAK "
            "(independence from the extra-select field unpinned)."
        ),
        "witness": _witness(_rq(False, False, False, True)),
    },
    {
        # Direction (D2): always narrow, ignoring explicit projection. Correct
        # on the not-projected sub-domain but over-fires on an explicitly
        # projected query, which must be left with its chosen columns.
        "id": "always-narrow",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl("    return true"),
        "refinement": (
            "this drops the guard entirely and narrows every rhs subquery. Its "
            "faithful real counterpart reduces even a subquery whose caller "
            "explicitly projected its output columns down to a single column, "
            "overriding the caller's chosen selection and changing the emitted "
            "SQL / result rows of that subquery. The narrowing exists exactly to "
            "fire only when the output columns are UNdefined; forcing it always "
            "regresses the behaviour of an explicitly-projected rhs subquery. A "
            "faithful patch that always narrows would change results for that "
            "sub-domain and would NOT preserve the required behaviour."
        ),
        "rationale": (
            "REJECT from `narrow = ! q.explicitlyProjected`: at "
            "(explicitlyProjected=T, others F) the spec requires narrow=false "
            "(already designated), but the rival returns true. Refuted at "
            "(T,F,F,F) — the only witness holding explicitlyProjected=true, "
            "exercising direction (D2) designates=>not-narrow. If it verified => "
            "SPEC-TOO-WEAK (the (D2) direction would be unpinned)."
        ),
        "witness": _witness(_rq(True, False, False, False)),
    },
    {
        # Direction (D1): never narrow. The other pre-change failure surface —
        # a subquery whose columns are undefined is left multi-column.
        "id": "never-narrow",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl("    return false"),
        "refinement": (
            "this never narrows any rhs subquery. Its faithful real counterpart "
            "removes the column reduction, so a membership subquery whose output "
            "columns were never explicitly projected is left returning all its "
            "columns; the __in comparison then raises "
            "'sub-select returns N columns - expected 1' on exactly the "
            "annotate()+alias() subquery the F2P exercises. The F2P subquery test "
            "asserts the queryset resolves, so it would NOT resolve — this is the "
            "(D1) direction of the same fix."
        ),
        "rationale": (
            "REJECT from `narrow = ! q.explicitlyProjected`: at "
            "(explicitlyProjected=F, others F) the spec requires narrow=true (not "
            "designated), but the rival returns false. Refuted at (F,F,F,F) — the "
            "all-false baseline, exercising direction (D1) not-designated=>narrow "
            "with none of the decoy fields set (so the violation is squarely the "
            "(D1) clause). If it verified => SPEC-TOO-WEAK (the (D1) direction "
            "would be unpinned)."
        ),
        "witness": _witness(_rq(False, False, False, False)),
    },

    # =====================================================================
    # INDEPENDENCE, THE OTHER DIRECTION (added by the G-PBT audit). The three
    # "coupling" rivals above all refute at explicitlyProjected=FALSE, so they
    # pin only the half of independence (I) in which a decoy field wrongly
    # ADDS designation. The mirror half — a decoy field wrongly REMOVING a
    # designation the caller did establish — was unattacked: before these three
    # cases no witness point held explicitlyProjected=true together with any
    # decoy field set (the only projected=true point was always-narrow's
    # (T,F,F,F), all decoys clear). A rival that honours explicit projection
    # EXCEPT when a decoy field happens to be set is wrong on exactly that
    # unwitnessed sub-domain, and each of the three below was confirmed by real
    # builds to be rejected and refuted at its point (rival elaborates, gold's
    # `decide` proves the claim false).
    # =====================================================================
    {
        "id": "annot-overrides-projection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let designated := q.explicitlyProjected && !q.carriesAnnotations\n"
            "    return !designated"),
        "refinement": (
            "this lets the annotation field VETO an explicit projection: a "
            "subquery whose caller did explicitly choose its output columns is "
            "nonetheless treated as not designating them as soon as it also "
            "carries annotation columns, so it gets narrowed to one column. Its "
            "faithful real counterpart overrides the caller's own chosen "
            "selection for every explicitly-projected subquery that also carries "
            "annotation columns — the annotate()-then-project shape — silently "
            "reducing a multi-column selection the caller asked for to a single "
            "column and changing that subquery's emitted SQL and result rows. "
            "The durable fix makes the decision read the explicit-projection "
            "state ALONE; a patch in which an annotation column can still "
            "cancel that state keeps exactly the mask-peeking coupling the fix "
            "removes, merely with the opposite sign, so it is an incomplete port "
            "of the fix."
        ),
        "rationale": (
            "REJECT from the single clause `narrow = ! q.explicitlyProjected`: at "
            "(explicitlyProjected=T, carriesAnnotations=T, others F) the spec "
            "requires narrow=false (the columns ARE designated, and the "
            "annotation field is irrelevant to that), but the rival's conjunction "
            "sees the annotation field and returns true. Refuted at (T,F,T,F) — a "
            "point no other witness reaches: it is the ONLY case pairing "
            "explicitlyProjected=true with a decoy field set, which is what pins "
            "independence (I) in the designation-PRESERVING direction. If it "
            "verified => SPEC-TOO-WEAK (a decoy field could still cancel an "
            "explicit projection)."
        ),
        "witness": _witness(_rq(True, False, True, False)),
    },
    {
        "id": "select-overrides-projection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let designated := q.explicitlyProjected && !q.hasExplicitSelectColumns\n"
            "    return !designated"),
        "refinement": (
            "the mirror of couples-select in the designation-preserving "
            "direction: the explicit select-column list VETOES an explicit "
            "projection rather than standing in for one. Its faithful real "
            "counterpart re-narrows a subquery whose caller explicitly projected "
            "its output columns whenever that query also carries a select-column "
            "list — which an explicitly projected query typically does — so the "
            "caller's chosen multi-column selection is discarded and the "
            "subquery's SQL and result rows change on that sub-domain. The fix's "
            "durability guarantee is that the decision consults NO internal "
            "column-state mask in either direction; retaining this veto leaves "
            "the same fragility with its sign flipped."
        ),
        "rationale": (
            "REJECT from `narrow = ! q.explicitlyProjected`: at "
            "(explicitlyProjected=T, hasExplicitSelectColumns=T, others F) the "
            "spec requires narrow=false, but the rival returns true. Refuted at "
            "(T,T,F,F) — a fifth-field-combination point distinct from every "
            "other witness, pinning that the SELECT-LIST field cannot cancel a "
            "designation either. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(_rq(True, True, False, False)),
    },
    {
        "id": "extra-overrides-projection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let designated := q.explicitlyProjected && !q.carriesExtraSelections\n"
            "    return !designated"),
        "refinement": (
            "the mirror of couples-extra in the designation-preserving "
            "direction: extra raw-select columns VETO an explicit projection. "
            "Its faithful real counterpart narrows an explicitly-projected "
            "subquery that also carries extra raw-select columns, overriding the "
            "caller's chosen output columns and changing that subquery's emitted "
            "SQL on the extra-selection sub-domain. As with the other two vetoes, "
            "a patch that keeps it has not actually decoupled the decision from "
            "the internal column-state masks — it has only changed which way the "
            "coupling points — so it is an incomplete port of the durable fix."
        ),
        "rationale": (
            "REJECT from `narrow = ! q.explicitlyProjected`: at "
            "(explicitlyProjected=T, carriesExtraSelections=T, others F) the spec "
            "requires narrow=false, but the rival returns true. Refuted at "
            "(T,F,F,T) — again a point no other witness reaches, pinning that the "
            "EXTRA-SELECT field cannot cancel a designation. Together with "
            "annot-overrides-projection and select-overrides-projection this "
            "completes independence (I) as a TWO-SIDED claim: no decoy field may "
            "add designation (the three couples-* rivals) and none may remove it "
            "(these three). If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(_rq(True, False, False, True)),
    },

    # =====================================================================
    # DECOY CO-OCCURRENCE (added by the second G-PBT audit). All eight rivals
    # above deviate from the frozen decision on a region reachable by moving ONE
    # decoy field, so every one of them is refutable at a point where at most one
    # decoy is set. A rival whose veto needs TWO decoys to co-occur is wrong only
    # on the part of the carrier where that conjunction holds — a region none of
    # the eight witness points touches (they use at most one true decoy each).
    # This closes it: the veto fires only when annotation columns AND extra raw
    # selections are BOTH present, so the rival agrees with the frozen decision
    # at all eight existing witness points and diverges only at (T,F,T,T) /
    # (T,T,T,T). Confirmed with real builds: the variant is rejected, and the
    # witness elaborates against the rival while `decide` refutes the same claim
    # against the frozen solution.
    # =====================================================================
    {
        "id": "compound-decoy-veto",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    let designated :=\n"
            "      q.explicitlyProjected && !(q.carriesAnnotations && q.carriesExtraSelections)\n"
            "    return !designated"),
        "refinement": (
            "a CONJUNCTIVE veto: an explicit projection is honoured unless the "
            "query happens to carry both annotation columns and extra raw-select "
            "columns at once, in which case the decision cancels the designation "
            "and narrows anyway. Its faithful real counterpart is a patch that "
            "decoupled the decision from each internal column-state mask "
            "individually but left a residual compound guard, so it re-narrows an "
            "explicitly-projected subquery on exactly the doubly-decorated "
            "sub-domain — discarding the caller's chosen multi-column output and "
            "changing that subquery's emitted SQL and result rows there. It is "
            "strictly harder to catch than the single-field vetoes: it agrees "
            "with the durable decision everywhere the other rivals are refuted, "
            "so it is an incomplete port of the fix that the rest of the battery "
            "would have passed over."
        ),
        "rationale": (
            "REJECT from `narrow = ! q.explicitlyProjected`: at "
            "(explicitlyProjected=T, carriesAnnotations=T, carriesExtraSelections=T) "
            "the spec requires narrow=false — the columns ARE designated and "
            "neither decoy, alone or together, bears on that — but the rival's "
            "compound veto returns true. Refuted at (T,F,T,T), a point NO other "
            "witness reaches and which no single-decoy rival can be refuted at. "
            "This is what makes independence (I) a claim about the decoy fields "
            "JOINTLY rather than one at a time: the previous eight witnesses all "
            "hold at most one decoy true, so a coupling that requires two decoys "
            "to co-occur was unattacked. If it verified => SPEC-TOO-WEAK (a "
            "compound decoy conjunction could still cancel an explicit "
            "projection)."
        ),
        "witness": _witness(_rq(True, False, True, True)),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus an EMPTY AXIOM lane, over
# THREE MUTATING operations on a minimal Query twin:
#   * project_columns             — the explicit-projection state update
#     (returned column list, flag set, auxiliary structure cleared);
#   * attach_auxiliary_expressions — the annotate/alias state update, carrying
#     THE reported bug in its frame clause (flag must equal its old value) and a
#     value frame over the SELECT column list;
#   * prepare_in_rhs              — the guarded rhs-narrowing routine (a
#     projection call, a pk-target guard, value-grounded narrowed-to-column and
#     no-narrow-implication clauses).
#
# THIS bundle models only the purely-functional CORE the fix turns on: the
# narrowing DECISION itself (the guard `not <stored has-fields flag>`) as a pure
# boolean function `narrowRhsSubquery : RhsQuery -> Bool` with the single clause
# `narrow = ! explicitlyProjected` (mapping.md §1). It models NONE of the
# mutations those operations perform — no returned column list, no cleared/
# preserved auxiliary structure, no flag write, no narrowed-to column value, no
# mut state. The decision's four inputs are FREE booleans. So most nagini cases,
# attached to a mutation's value footprint, have no counterpart on this carrier —
# carrier narrowing, NOT a coverage gap. Every nagini case is accounted for.
#
#   nagini case                        -> here
#   -----------------------------------------------------------------------
#   pos-project-reorder-no-reset       -> (none)              NO CARRIER (mutation)
#   pos-rhs-inline-projection          -> (none)              NO CARRIER (mutation)
#                                         [correct-reshape spirit carried by
#                                          pos-spec-fn / pos-ite-form]
#   admiss-rhs-narrow-reachable        -> admiss-f2p-decision RE-AIMED (audit 2)
#   weak-aux-recouples-flag            -> recouples           PORTED (THE bug)
#   weak-rhs-narrow-without-flag       -> (none)              NO CARRIER (flag write)
#   weak-rhs-overfires-on-pk-target    -> (none)              NO CARRIER (pk guard)
#   faith-aux-preserved-in-project     -> (none)              NO CARRIER + FRAME
#   frame-cols-in-aux                  -> (none)              NO CARRIER + FRAME
#   weak-rhs-wrong-column              -> (none)              NO CARRIER (column value)
#   (no nagini counterpart)            -> couples-select      NEW (independence I)
#   (no nagini counterpart)            -> couples-extra       NEW (independence I)
#   (no nagini counterpart)            -> always-narrow       NEW (direction D2)
#   (no nagini counterpart)            -> never-narrow        NEW (direction D1)
#   (no nagini counterpart)            -> pos-decoy-branch    AUDIT (reads a decoy,
#                                                             correct value)
#   (no nagini counterpart)            -> annot-overrides-projection
#                                                             AUDIT (I, other side)
#   (no nagini counterpart)            -> select-overrides-projection
#                                                             AUDIT (I, other side)
#   (no nagini counterpart)            -> extra-overrides-projection
#                                                             AUDIT (I, other side)
#   (no nagini counterpart)            -> compound-decoy-veto AUDIT-2 (I, JOINT)
#   AXIOM_TESTS (0)                    -> (none)              EMPTY (G-AX)
#
# PORTED (1): weak-aux-recouples-flag is THE reported bug — the pre-change
#   derived heuristic that re-coupled the has-fields decision to a disjunction
#   over the query's select-list / annotation / extra-selection masks. On this
#   carrier that IS the modeled decision, and the rival `recouples` is exactly
#   this bundle's Solution_prepatch skeleton. Its refinement is intact (the
#   annotate()+alias() subquery reports designated and the sub-select returns N
#   columns -> the F2P subquery test does not resolve).
# NO CARRIER — MUTATION VALUE FOOTPRINT (5): pos-project-reorder-no-reset and
#   pos-rhs-inline-projection reshape project_columns / prepare_in_rhs, whose
#   returned column list, cleared auxiliary structure, flag write and mask
#   clearing are unmodeled here; weak-rhs-narrow-without-flag attacks the flag
#   SIDE EFFECT of the narrowing routine (whether prepare_in_rhs sets the stored
#   flag) — this bundle models the decision that READS the flag as a free input,
#   not the write; weak-rhs-wrong-column attacks the value-grounded narrowed-to
#   column ([0]==target) — this decision returns a Bool, not a column;
#   weak-rhs-overfires-on-pk-target drops a guard on a property of the
#   comparison's TARGET field, a SEPARATE conjunct of the real routine that
#   mapping.md does not model (only the column-state guard is modeled), and for
#   which this carrier has no input at all — RhsQuery's four fields are all
#   query column-state booleans, so there is no binder to vary. All five
#   attach to observations the carrier does not carry. Omitted because the
#   modeled surface does not include that behaviour, NOT because it was hard to
#   prove.
# FRAME (2): faith-aux-preserved-in-project (project must CLEAR the auxiliary
#   structure) and frame-cols-in-aux (annotate/alias must NOT touch the SELECT
#   columns) are VALUE-FRAME rivals over the mutations' fields. There is no heap,
#   no aliasing, no mut binder, and neither the auxiliary structure nor the
#   SELECT column list is a modeled observation, so there is no frame to violate.
#   No substitute probe fabricated (porting map: FRAME class vacuous here).
# RE-AIMED (admissibility, corrected by the second audit): the nagini
#   admiss-rhs-narrow-reachable probe establishes the narrowing branch is
#   reachable under its Requires. The FIRST audit recorded this lane as VACUOUS
#   because this method has no `require` clause (pre-conditions region empty).
#   That reason does not hold: "the frozen obligation has no precondition" is not
#   a demonstration of vacuity, it just means the nagini spelling does not
#   transfer. On a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the
#   obligation being unsatisfiable — or degenerately satisfiable — at exactly an
#   F2P-shaped input, which is a real risk here and is testable. The lane is now
#   carried by `admiss-f2p-decision`, which discharges the obligation by
#   EVALUATION at the failing-scenario input (P=F,S=F,A=T,E=F) as an in-region
#   assert, plus a second conjunct at (P=T,S=F,A=T,E=F) that forces the opposite
#   value so no constant decision could satisfy both, before closing the frozen
#   obligation verbatim. Confirmed live by a real build: flipping the second
#   conjunct's polarity does NOT verify.
# NEW (4, no direct nagini counterpart): the nagini rivals live on the MUTATIONS;
#   this carrier's decision has its own strength surface — the two-sided clause
#   plus INDEPENDENCE from the three decoy fields — with no single nagini rival
#   per facet. couples-select and couples-extra isolate dependence on the
#   select-list and extra-select fields respectively (the first and third
#   disjuncts of the pre-change heuristic that recouples carries whole),
#   pinning independence (I); always-narrow and never-narrow pin the two
#   directions (D2)/(D1) of the sole clause. All four are real divergences with
#   machine-checked witnesses (each ELABORATES against its rival and FAILS
#   against gold), not fabricated wrongness.
#
#   HONESTY NOTE on the two independence rivals. recouples and never-narrow are
#   F2P-airtight: their faithful patches reproduce the exact
#   'sub-select returns N columns' failure on the annotate()+alias() subquery.
#   always-narrow's faithful patch over-narrows an explicitly-projected rhs
#   (a change on a sub-domain the general contract forbids). couples-select and
#   couples-extra are SPEC-INDEPENDENCE rivals: their direct link to the two
#   named F2P tests is through the fix's general durability guarantee (the fix
#   removed consultation of ALL internal masks, not only the annotation mask)
#   rather than through those two specific tests, which exercise only the
#   annotation field. They are shipped because the spec's strength claim IS the
#   independence, and refuting them demonstrates the postcondition pins
#   `narrow = ! explicitlyProjected` exclusively — no residual dependence on the
#   select-list or extra-select fields. Both were verified to discriminate.
#
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# CLAUSE / BINDER / POINT COVERAGE. The postcondition is a single top-level
#   clause `narrow = narrowsToSingleColumn q = ! q.explicitlyProjected`, attacked
#   from both directions (D1 by never-narrow, D2 by always-narrow) and defended
#   for its independence from all three decoy fields in BOTH directions:
#   a decoy may not ADD designation (recouples/annotation,
#   couples-select/select, couples-extra/extra, all at explicitlyProjected=F)
#   and may not REMOVE one (annot-/select-/extra-overrides-projection, all at
#   explicitlyProjected=T). All three positives defend the clause, the third by
#   reading a decoy field while returning the correct value — so a couples-*
#   rival is rejected for its DECISION, not for touching a field.
#   NINE DISTINCT reject witness points, one per rival, no two shared:
#     (F,F,T,F) recouples                    (T,F,T,F) annot-overrides
#     (F,T,F,F) couples-select               (T,T,F,F) select-overrides
#     (F,F,F,T) couples-extra                (T,F,F,T) extra-overrides
#     (T,F,F,F) always-narrow                (F,F,F,F) never-narrow
#     (T,F,T,T) compound-decoy-veto
#   Each of the four carrier fields is moved across {false,true}; explicitly-
#   Projected is paired with EACH decoy field at both of its values; and one
#   point sets TWO decoys at once. That last point is not decoration: the first
#   eight all hold at most one decoy true, so a rival whose deviation requires a
#   CONJUNCTION of decoys agrees with the frozen decision at every one of them.
#   No binder is held constant across all witnesses.
#
#   HONEST LIMIT of the point set. Nine of the carrier's 16 points carry a
#   witness; the battery does NOT claim the remaining seven are unreachable by
#   some rival's deviation, only that every deviation the modeled fix's failure
#   modes produce — each decoy adding designation, each removing one, either
#   direction of the clause, and a two-decoy conjunction — is refuted at a point
#   here. The earlier claim that "no sub-domain of the 16-point carrier is left
#   where a rival could differ unwitnessed" was FALSE and is retracted: the
#   second audit built a rival (the compound veto, now shipped) that differed from
#   the frozen decision only where two decoys co-occur, which no then-existing
#   witness reached.
#
#   AUDIT NOTE (why the last four cases exist). The originally ported battery
#   had all five of its reject witnesses at points where AT MOST one field was
#   true, and the only explicitlyProjected=true point had every decoy clear. So
#   the sub-domain "explicitly projected AND carrying decoy columns" carried no
#   witness at all, and independence (I) was demonstrated in one direction only.
#   The three *-overrides-projection rivals are wrong exactly and only on that
#   sub-domain; each was confirmed by real builds to be rejected by the frozen
#   script and refuted by its witness (the witness elaborates against the rival,
#   and against the frozen solution `decide` proves the claim false — a semantic
#   refutation, not a syntactic build error). Independently, the frozen spec was
#   probed for exactness: it admits the frozen decision at all 16 carrier points
#   and pins `narrow` uniquely at each, and ten further wrong impls beyond those
#   listed here (single-point deviations, conjunctive and inverted forms, and
#   decoy-only decisions) were all rejected — no SPEC-TOO-WEAK hole was found.
#   Four correct reshapes beyond the positives above also verify, so no
#   SPEC-TOO-STRONG hole either.
#
#   AUDIT-2 NOTE (the second, independent audit). It re-ran every case from
#   scratch: all 11 variants (3 verify / 8 reject, matching), all 8 witnesses on
#   both sides (rival exit 0, gold exit 1, every gold failure the `decide`-refutes
#   form naming the concrete record), and a FORGERY control per witness — the
#   same file with the claim FLIPPED (`= true` instead of `= false`) builds clean
#   on gold (exit 0) and fails on the rival (exit 1), exactly inverting the
#   witness pair. So each gold exit code tracks WHAT IS CLAIMED rather than being
#   a constant property of the gold file, which is what makes these refutations
#   admissible evidence rather than incidental build breakage.
#   It then landed two additions and two prose corrections:
#     * admiss-f2p-decision — the admissibility lane the first audit dropped for a
#       reason that does not hold (see RE-AIMED above);
#     * compound-decoy-veto — the joint-independence rival, from a new wrong impl
#       that the eight existing witnesses could not have refuted;
#     * retracted the false "no unwitnessed sub-domain" coverage claim above;
#     * removed a repo identifier from the NO CARRIER note (leak discipline —
#       this file ships and G-LEAK does not screen it).
#   Six further NEW wrong impls (three single-point deviations aimed at points no
#   witness held, a decoy-majority vote, the compound veto, and an xor-with-decoy)
#   were ALL rejected; five further NEW correct reshapes (match-on-boolean, a
#   cancelling tautological conjunction, a three-decoy branch tree, equality-
#   against-false, and the spec's own `designatesOutputColumns` under a retuned
#   tactic body) ALL verify. No spec hole in either direction.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the decision is modeled directly, not delegated to an oracle), so there
# is nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
