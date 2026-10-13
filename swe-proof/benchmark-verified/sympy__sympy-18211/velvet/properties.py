"""properties.py — G-PBT falsification battery for sympy__sympy-18211 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct relationAsSet`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over an opaque relation handle):

  relationAsSet (rel)   ensures out = asSetSpec rel

``rel`` is the single INPUT binder. It is an opaque handle: the spec observes it
ONLY through two opaque projections — a univariate-relation solver
``solveUnivariate rel`` (``Except.ok h`` = it produced an explicit solution set
carried verbatim as an opaque handle ``h``; ``Except.error cannotSolve`` = it
reports it cannot solve the relation; ``Except.error other`` = any other failure)
and the explicit unevaluated condition set ``conditionOverReals rel`` built
ENTIRELY from the relation itself. ``asSetSpec`` pins the whole outcome as a
total function of those observations, with THREE independent top-level legs:

  (L1) solveUnivariate = ok h            -> out = ok (solverSet h)            [set verbatim]
  (L2) solveUnivariate = error cannotSolve -> out = ok (conditionOverReals rel) [FALLBACK]
  (L3) solveUnivariate = error other       -> out = error other                [propagate]

L2 is the discriminating behaviour the public issue reports: a cannot-solve
report must NOT escape; instead the routine returns the explicit unevaluated
condition set over the reals built from the relation. A wrong rival must violate
one of L1-L3.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION — VACUOUS here. The nagini class exists because an input
    field may carry a fractional heap permission an impl can overwrite (the
    sibling's ``rel.solvability = 1`` write under a half-permission). This backend
    is referentially transparent and this bundle declares NO ``mut`` binder:
    ``rel`` is an immutable value, there is no heap and no aliasing, so there is
    no read-only input to mutate and no substitute probe to build. Not
    fabricated.
  * DIVERGENCE / NON-TERMINATION — NO SPEC HOLE, but not shippable as a
    witnessed reject case. This bundle sets
    ``loom.semantics.termination "total"``, under which a postcondition is claimed of
    ALL runs, not only terminating ones, so the verifier discharges a termination
    obligation and a diverging rival is genuinely REJECTED rather than vacuously
    accepted. (An earlier version of this bullet identified ``"partial"`` as "the
    setting an internal findings doc reports a hole for". No bundle carries it: all 500
    velvet bundles set ``"total"`` and open ``TotalCorrectness``.) Measured, not
    assumed: splicing ``while i < 1 do i := i`` (a loop with no decreasing measure)
    after the frozen leg-dispatch is rejected, exit 1, ``error: Decreasing annotations
    are required in total correctness semantics``; and the sharper shape that CARRIES a
    measure which does not decrease (``while q > 0 / invariant 0 ≤ q /
    done_with q = 0 / decreasing q``, body ``q := q``) is REJECTED on the measure's own
    goal - ``case «decreasing_1: q»``, residual ``⊢ q < q``. So the spec is NOT weak
    here, and the refusal is not merely the annotation linter.
    It is nonetheless omitted from the reject lane, for a demonstrated reason that
    is about the WITNESS mechanism and not about difficulty: a witness file is the
    variant with its ``prove_correct`` block stripped and the snippet appended, so
    that same total-correctness linter error fires INSIDE the witness file too and
    the rival-side build — the half that must SUCCEED for the case to count —
    fails (exit 1, same message, re-measured). The case would therefore record
    ``witness-unproven`` (INCONCLUSIVE), which forces MALFORMED-TESTS and fails the
    whole battery, rather than recording a refutation. ``witness_reference`` does
    not help: it substitutes the GOLD-side subject, and the failing build here is
    the rival's. Reported rather than landed; no ``set_option`` workaround is
    available, since flipping the linter would have to edit the spec region and
    would leave variant scope.
  * PARTIAL-DOMAIN / VALUE — APPLIES. ``rel`` is only ever observed through
    ``solveUnivariate`` (three outcomes) and ``conditionOverReals`` (one grounded
    set); a rival right on part of that observation space but diverging on a
    sub-region is the natural falsifier. The rivals below partition the space
    exactly along L1-L3, and L2 is attacked three independent ways (ok-vs-error,
    which constructor, and grounding of the argument).
  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense. ``asSetSpec`` is a total
    ``def`` in the ``pure`` region written directly over ``solveUnivariate`` and
    ``conditionOverReals`` — the two observations the impl itself branches on and
    builds — not an opaque answer-key the impl could echo without doing the work.
    The fallback set is GROUNDED in the input (``conditionOverReals rel``,
    directive 8), so an impl that fabricated a different set on the cannot-solve
    leg is refutable (R2b, R2c). The ``axioms`` region declares no ``axiom`` —
    ``solveUnivariate`` is ``opaque`` with no ``ensures`` — so there is no consumed
    contract to attack. Honest positive controls stand in for the ungrounded-echo
    probe.

THE WITNESS ON AN OPAQUE CARRIER. ``rel`` feeds only opaque functions, so a
``decide`` on a concrete literal (``relationAsSetTester 0``) gets STUCK: nothing
reduces ``solveUnivariate 0``. A witness therefore cannot pin ``rel`` to a value;
instead it HYPOTHESISES the solver's outcome at a symbolic ``rel``
(``solveUnivariate rel = …`` — exactly the sub-region the rival's leg is wrong on)
and shows the extracted program's output differs from ``asSetSpec rel`` there.
Reaching the program uses Velvet's own extractor (``extract_program_for`` gives
``relationAsSetExec = NonDetT.run ∘ relationAsSet``, and
``NonDetT.run (pure x) = DivM.res x``). The snippet is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict, and it must (1) elaborate against the rival and (2) FAIL against the
frozen solution — verified for each rival below (the gold reduces the very same
goal to ``False`` with no remaining assumptions to close it). No ``sorry``/
``admit``/``native_decide``/``axiom``: the single hypothesis is an ordinary
equality of the opaque solver outcome, not an assumption of the conclusion, and
one hypothesis per witness keeps the assumptions jointly satisfiable (no
contradictory pair).

WITNESS PLACEMENT / BINDER COVERAGE. Because ``rel`` is observed through
``solveUnivariate``, "varying the binder" means varying that outcome. The rivals
probe ``solveUnivariate`` at all THREE outcomes {ok, cannotSolve, other}, so the
sole input's observation is never held fixed across the battery. The grounding
rival (R2c) additionally distinguishes ``conditionOverReals rel`` from
``conditionOverReals (rel+1)``, exercising the fallback's dependence on ``rel``
itself.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the unchanged solver
is ``opaque`` with no asserted ``ensures``, owed no contract). There is no
axiom-soundness / axiom-containment obligation to probe here, and the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-18211"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole leg-dispatch `let`, wholly inside the one
# ---- `-- impl-start` / `-- impl-end` region and unique in the file (both facts
# ---- asserted at load by _swap). Every variant reshapes exactly this block. ----
_IMPL = (
    "    let result : Except SolveErr SetVal :=\n"
    "      match solveUnivariate rel with\n"
    "      | Except.ok h => Except.ok (SetVal.solverSet h)\n"
    "      | Except.error SolveErr.cannotSolve =>\n"
    "          Except.ok (SetVal.conditionOverReals rel)\n"
    "      | Except.error SolveErr.other => Except.error SolveErr.other"
)

# ---- the frozen `prove_correct` tactic body. A positive control that reshapes
# ---- the impl into a form the frozen script no longer closes may RETUNE this
# ---- body (it is elided from the consumer spec view) WITHOUT touching the spec
# ---- or dropping the obligation — the `prove_correct relationAsSet by` header
# ---- statement stays byte-identical. Unique in the file. ----
_PROOF = (
    "prove_correct relationAsSet by\n"
    "  loom_solve\n"
    "  simp_all [asSetSpec]\n"
)


def _swap2(a_old, a_new, p_old, p_new):
    """Reshape the impl region AND retune the prove_correct tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), p_old, p_new)


# ---- the admissibility case keeps the frozen leg-dispatch VERBATIM and appends
# ---- an in-region `assert` after it, so the method's own obligation still
# ---- discharges exactly as the frozen file's does; only the tactic body is
# ---- retuned (elided from the consumer spec view) to clear the extra goal. ----
_ADMISS_ASSERT = (
    "\n"
    "    -- ADMISSIBILITY at the F2P-shaped point. The obligation must be\n"
    "    -- SATISFIABLE and NON-DEGENERATE exactly where the interesting scenario\n"
    "    -- lands: at an input the solver reports it CANNOT solve, the post-image\n"
    "    -- demands a NORMALLY-RETURNED condition set over the reals grounded in\n"
    "    -- this very relation, and specifically NOT the cannot-solve failure\n"
    "    -- escaping and NOT a solver-flavoured set.\n"
    "    assert (with_name_prefix `admiss\n"
    "      (solveUnivariate rel = Except.error SolveErr.cannotSolve →\n"
    "        asSetSpec rel = Except.ok (SetVal.conditionOverReals rel)\n"
    "        ∧ asSetSpec rel ≠ Except.error SolveErr.cannotSolve\n"
    "        ∧ asSetSpec rel ≠ Except.ok (SetVal.solverSet rel)))"
)

_PROOF_ADMISS = (
    "prove_correct relationAsSet by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | (intro hcs; simp [asSetSpec, hcs])\n"
    "    | simp_all [asSetSpec]\n"
)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- and its input is observed only through the opaque solver, so a witness
# ---- reaches the impl through Velvet's extractor and HYPOTHESISES the solver's
# ---- outcome at the sub-region the rival mishandles. `relationAsSetExec` is
# ---- `NonDetT.run (relationAsSet rel)`, which reduces to `DivM.res result`;
# ---- `≠ DivM.res (asSetSpec rel)` says the impl's output contradicts the
# ---- postcondition there. Checked in a file whose `prove_correct` block is
# ---- stripped, so no tactic script can interfere.
def _wit(hyps, rws):
    hyp_lines = "".join(f"\n    ({h})" for h in hyps)
    rw = ", ".join(rws)
    return (
        "extract_program_for relationAsSet\n\n"
        f"example (rel : Int){hyp_lines} :\n"
        "    relationAsSetExec rel ≠ DivM.res (asSetSpec rel) := by\n"
        "  unfold relationAsSetExec relationAsSet asSetSpec\n"
        f"  rw [{rw}]\n"
        "  simp [NonDetT.run, pure]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct reshape cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = asSetSpec rel`
    # obligation and only reshapes the executable leg-dispatch.
    # =====================================================================
    {
        "id": "pos-arms-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the same three-way outcome dispatch written with the `other`
        # arm before the `cannotSolve` arm. A `match` is order-insensitive on
        # disjoint constructors, so the computed outcome is identical on every
        # leg. The frozen script closes by `rfl` on the frozen arm order; the
        # reordered form needs an explicit split on the outcome, so the tactic
        # body is retuned (elided from the spec view) while the obligation
        # statement is byte-identical.
        "module": _swap2(
            _IMPL,
            "    let result : Except SolveErr SetVal :=\n"
            "      match solveUnivariate rel with\n"
            "      | Except.ok h => Except.ok (SetVal.solverSet h)\n"
            "      | Except.error SolveErr.other => Except.error SolveErr.other\n"
            "      | Except.error SolveErr.cannotSolve =>\n"
            "          Except.ok (SetVal.conditionOverReals rel)",
            _PROOF,
            "prove_correct relationAsSet by\n"
            "  loom_solve\n"
            "  unfold asSetSpec\n"
            "  cases solveUnivariate rel with\n"
            "  | ok h => rfl\n"
            "  | error e => cases e <;> rfl\n",
        ),
        "rationale": "reordering the disjoint outcome arms computes the same "
                     "`Except SolveErr SetVal` on every leg, so "
                     "`out = asSetSpec rel` still holds; a correct reshape must "
                     "verify (else SPEC-TOO-STRONG on arm order). Ports the "
                     "nagini pos-control-explicit-branch: a structurally-different "
                     "but correct dispatch that keeps every leg's output.",
    },
    {
        "id": "pos-error-kind-decided",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: collapse the two failure arms into ONE `Except.error e` arm and
        # recover the distinction by DECIDING the error kind with an `if` on the
        # derived `DecidableEq`, re-emitting `Except.error e` (not the literal
        # `SolveErr.other`) on the else branch. Correct on every leg — on the else
        # branch `e` is necessarily `other`, so `error e = error other` — but the
        # dispatch is no longer a constructor-pattern `match`, so the impl term is
        # NOT definitionally equal to the frozen one: `rfl` does not close
        # `ifKindTerm rel = goldTerm rel` (checked directly, exit 1). The frozen
        # `simp_all [asSetSpec]` body therefore fails, and the retuned body has to
        # discharge the `if` on the error leg genuinely (`cases e <;> simp`), which
        # is what makes this a load-bearing positive rather than a restatement.
        #
        # AUDIT NOTE — this case REPLACES an earlier `pos-fallback-hoisted`, which
        # hoisted the fallback set into a `let` before the dispatch. That reshape
        # was VACUOUS: a `let` bound to a term used once zeta-reduces, so the
        # hoisted impl term is DEFINITIONALLY EQUAL to the frozen one (`rfl` closes
        # `hoistedTerm rel = goldTerm rel`, exit 0) and the frozen tactic body
        # closed it unretuned. It verified honestly while exercising nothing the
        # frozen file does not already establish, so it could not have detected a
        # SPEC-TOO-STRONG on arm shape. This replacement is a reshape the carrier
        # can actually tell apart from gold.
        "module": _swap2(
            _IMPL,
            "    let result : Except SolveErr SetVal :=\n"
            "      match solveUnivariate rel with\n"
            "      | Except.ok h => Except.ok (SetVal.solverSet h)\n"
            "      | Except.error e =>\n"
            "          if e = SolveErr.cannotSolve then\n"
            "            Except.ok (SetVal.conditionOverReals rel)\n"
            "          else Except.error e",
            _PROOF,
            "prove_correct relationAsSet by\n"
            "  loom_solve\n"
            "  unfold asSetSpec\n"
            "  cases solveUnivariate rel with\n"
            "  | ok h => rfl\n"
            "  | error e => cases e <;> simp\n",
        ),
        "rationale": "deciding the failure kind with an `if` on the derived "
                     "`DecidableEq` and re-emitting `Except.error e` computes the "
                     "same `Except SolveErr SetVal` on all three legs (on the else "
                     "branch `e` is necessarily `other`), so `out = asSetSpec rel` "
                     "still holds; a correct reshape must verify (else "
                     "SPEC-TOO-STRONG on the dispatch form). Unlike a hoisted-`let` "
                     "reshape, this impl term is NOT definitionally equal to the "
                     "frozen one — `rfl` fails on it — so the positive is "
                     "load-bearing: the retuned body must prove the error leg "
                     "rather than restate it.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares NO `require` clause, so the sibling's
    # "the precondition accepts an F2P-shaped input" probe cannot be ported
    # literally: nothing could exclude any `rel`. The residual admissibility risk
    # on a TOTAL domain is the other direction — the post-image being
    # UNSATISFIABLE or DEGENERATE at exactly the interesting point, which reads
    # like a spec every impl meets when it is really one no impl can meet. This
    # case discharges that AT the F2P-shaped input (a relation the solver reports
    # it cannot solve — the sub-region the whole change exists for) as an in-region
    # `assert`, BEFORE the frozen obligation closes verbatim: on that leg the
    # post-image demands a normally-returned condition set grounded in this very
    # relation, and is NOT met by the failure escaping nor by a solver-flavoured
    # set. The frozen leg-dispatch is kept byte-identical so the method's own
    # `ensures` still discharges as it does in the frozen file; only the tactic
    # body is retuned to clear the extra goal.
    #
    # The assert is LIVE — machine-checked by the audit that added it, not
    # asserted by hand. Three deliberately FALSE variants of the same claim (the
    # fallback being the cannot-solve error; the post-image ALSO equal to that
    # error; the post-image equal to `solverSet rel`) each leave an unsolved goal
    # named `case «admiss_1: ...»` at exit 1, while the shipped claim verifies at
    # exit 0. So the case can fail, and what it would fail on is the post-image
    # degenerating at the F2P point.
    # =====================================================================
    {
        "id": "admiss-f2p-cannotsolve-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(_IMPL, _IMPL + _ADMISS_ASSERT, _PROOF, _PROOF_ADMISS),
        "rationale": "the obligation is SATISFIABLE and NON-DEGENERATE at the "
                     "F2P-shaped input. At a relation the solver reports it cannot "
                     "solve, the post-image pins `out` to "
                     "`ok (conditionOverReals rel)` — a set returned NORMALLY and "
                     "grounded in the relation passed in — and is met by neither "
                     "the cannot-solve failure escaping nor a `solverSet` result. "
                     "Discharged by evaluation as an in-region `assert` at that "
                     "concrete leg, with the frozen dispatch kept verbatim so the "
                     "method's own `ensures` closes as in the frozen file. If it "
                     "cannot discharge, the post-image is unsatisfiable/degenerate "
                     "exactly where the change matters (PRECOND-TOO-STRONG on a "
                     "total carrier). Ports the nagini admiss-f2p-undecided-shaped "
                     "onto the no-`require` carrier: same interesting input, the "
                     "obligation re-aimed from the precondition (which cannot "
                     "reject anything here) onto the post-image at that input.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete sub-region of the input's observation space, and the
    # refinement argument for why its faithful real counterpart would NOT
    # resolve the failing test.
    # =====================================================================

    # ---- L1: the solver-set-verbatim success leg ----
    {
        "id": "weak-success-alters-set",
        "kind": "uniqueness",
        "expect": "reject",
        # On a successful solve, perturbs the carried opaque set handle (`h + 1`)
        # instead of carrying it verbatim. Correct on both failure legs; wrong
        # exactly when the solver succeeds. Re-sites the nagini
        # partial-domain-fabricated-determined-fields (the determined branch must
        # return the solver's OWN returned set, not a fabricated one).
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except SolveErr SetVal :=\n"
            "      match solveUnivariate rel with\n"
            "      | Except.ok h => Except.ok (SetVal.solverSet (h + 1))\n"
            "      | Except.error SolveErr.cannotSolve =>\n"
            "          Except.ok (SetVal.conditionOverReals rel)\n"
            "      | Except.error SolveErr.other => Except.error SolveErr.other"),
        "refinement": "a counterpart that returned a rebuilt/substituted set "
                      "instead of the solver's own returned set on a solvable "
                      "relation would discard the genuine solution set. The "
                      "unchanged tests that observe the real solver sets on "
                      "solvable relations (e.g. a genuine interval union) compare "
                      "for equality and still fail. It would NOT resolve.",
        "rationale": "REJECT from L1 (`solveUnivariate = ok h -> out = ok "
                     "(solverSet h)`): at a successful outcome the impl carries a "
                     "perturbed handle where the post-image demands the handle "
                     "verbatim. Probes `solveUnivariate rel = ok`.",
        "witness": _wit(["h1 : solveUnivariate rel = Except.ok 0"], ["h1"]),
    },

    {
        "id": "weak-success-returns-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # On a successful solve it returns the CONDITION-SET fallback instead of the
        # solver's produced set — right constructor arity, wrong constructor. This
        # is the L1 half of the sibling's branch swap, which the port omitted as
        # "subsumed" by weak-success-alters-set. It is NOT subsumed:
        # weak-success-alters-set perturbs the handle INSIDE `solverSet`, so it only
        # pins the ARGUMENT of the success-leg constructor; nothing in the battery
        # pinned WHICH `SetVal` constructor the success leg must use. Added by audit
        # for that clause.
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except SolveErr SetVal :=\n"
            "      match solveUnivariate rel with\n"
            "      | Except.ok h => Except.ok (SetVal.conditionOverReals rel)\n"
            "      | Except.error SolveErr.cannotSolve =>\n"
            "          Except.ok (SetVal.conditionOverReals rel)\n"
            "      | Except.error SolveErr.other => Except.error SolveErr.other"),
        "refinement": "a counterpart that returned the explicit unevaluated "
                      "condition set even when the solver DID produce an explicit "
                      "solution set would discard every genuine solution set: every "
                      "solvable relation would come back as the symbolic set. The "
                      "unchanged tests that observe real solver sets on solvable "
                      "relations (e.g. a genuine interval union) compare for "
                      "equality and still fail. It would NOT resolve.",
        "rationale": "REJECT from L1 (`solveUnivariate = ok h -> out = ok "
                     "(solverSet h)`): at a successful outcome the impl returns the "
                     "`conditionOverReals` constructor where the post-image demands "
                     "the `solverSet` one. If this verifies, the success leg's "
                     "returned-set KIND is unpinned — the clause "
                     "weak-success-alters-set does not reach, since perturbing the "
                     "handle only pins that constructor's argument. Probes "
                     "`solveUnivariate rel = ok`.",
        "witness": _wit(["h1 : solveUnivariate rel = Except.ok 0"], ["h1"]),
    },

    # ---- L2: the cannot-solve fallback leg (the discriminating F2P behaviour) ----
    {
        "id": "weak-cannotsolve-escapes",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-PATCH behaviour: the solver's result is returned directly, so a
        # cannot-solve failure escapes as `error cannotSolve` instead of becoming
        # the condition-set fallback. Correct on L1 and L3; wrong exactly on the
        # cannot-solve leg. This is the canonical verify-not-resolve rival
        # (== Solution_prepatch.lean / G-DIFF); re-sites the nagini
        # control-flow-no-handler-totality (the failure must not escape).
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except SolveErr SetVal :=\n"
            "      match solveUnivariate rel with\n"
            "      | Except.ok h => Except.ok (SetVal.solverSet h)\n"
            "      | Except.error e => Except.error e"),
        "refinement": "this is the pre-patch control flow: the solver result is "
                      "returned directly, so a cannot-solve report propagates out "
                      "of the routine instead of yielding the explicit condition "
                      "set over the reals. On the failing input the routine raises "
                      "where the desired behaviour returns the condition set, so "
                      "the failing test that asserts the returned condition set "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from L2 (`solveUnivariate = error cannotSolve -> out "
                     "= ok (conditionOverReals rel)`): on the cannot-solve outcome "
                     "the impl re-propagates the failure where the post-image "
                     "demands the condition-set fallback returned normally. Probes "
                     "`solveUnivariate rel = error cannotSolve`.",
        "witness": _wit(
            ["h1 : solveUnivariate rel = Except.error SolveErr.cannotSolve"],
            ["h1"]),
    },
    {
        "id": "weak-fallback-not-condition-set",
        "kind": "uniqueness",
        "expect": "reject",
        # On the cannot-solve leg it returns normally (does not escape) but builds
        # a SOLVER-flavoured set (`solverSet rel`) rather than the explicit
        # condition set over the reals. Correct on L1, L3, and on the ok/error
        # dichotomy of L2; wrong on WHICH set the fallback is. Re-sites the nagini
        # uniqueness-fallback-not-flagged (the fallback must be the symbolic
        # condition set, not a genuine-solver-flavoured set).
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except SolveErr SetVal :=\n"
            "      match solveUnivariate rel with\n"
            "      | Except.ok h => Except.ok (SetVal.solverSet h)\n"
            "      | Except.error SolveErr.cannotSolve =>\n"
            "          Except.ok (SetVal.solverSet rel)\n"
            "      | Except.error SolveErr.other => Except.error SolveErr.other"),
        "refinement": "a counterpart that, on a cannot-solve report, returned a "
                      "concrete solver-flavoured set instead of the explicit "
                      "unevaluated condition set over the reals would produce the "
                      "wrong kind of set on the failing relation. The failing test "
                      "compares the result against the explicit condition set and "
                      "still fails (it now sees a different set object). It would "
                      "NOT resolve.",
        "rationale": "REJECT from L2 (`... -> out = ok (conditionOverReals rel)`): "
                     "on the cannot-solve outcome the impl returns `solverSet rel` "
                     "where the post-image demands `conditionOverReals rel` — the "
                     "two constructors are distinct, so the returned-set KIND is "
                     "unpinned if this verifies. Probes `solveUnivariate rel = "
                     "error cannotSolve`.",
        "witness": _wit(
            ["h1 : solveUnivariate rel = Except.error SolveErr.cannotSolve"],
            ["h1"]),
    },
    {
        "id": "weak-fallback-ungrounded",
        "kind": "uniqueness",
        "expect": "reject",
        # On the cannot-solve leg it builds the condition set from a DIFFERENT
        # relation handle (`rel + 1`) rather than the actual input `rel`. Correct
        # on the ok/error dichotomy and on the constructor; wrong on the GROUNDING
        # of the fallback in the input (directive 8). Re-sites the nagini
        # partial-domain-wrong-fallback-cond (the fallback's defining condition
        # must be the relation itself, not some other token). Distinguishes
        # `conditionOverReals rel` from `conditionOverReals (rel+1)`, exercising
        # the fallback's dependence on `rel`.
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except SolveErr SetVal :=\n"
            "      match solveUnivariate rel with\n"
            "      | Except.ok h => Except.ok (SetVal.solverSet h)\n"
            "      | Except.error SolveErr.cannotSolve =>\n"
            "          Except.ok (SetVal.conditionOverReals (rel + 1))\n"
            "      | Except.error SolveErr.other => Except.error SolveErr.other"),
        "refinement": "a counterpart that built the condition set from a relation "
                      "other than the one being solved would return the explicit "
                      "unevaluated set of a DIFFERENT relation. The failing test "
                      "asserts the condition set is built from the very relation "
                      "passed in, so a set defined by a different relation still "
                      "fails the equality. It would NOT resolve.",
        "rationale": "REJECT from L2 grounding (`... -> out = ok "
                     "(conditionOverReals rel)`): the fallback is pinned to the "
                     "input `rel` (directive 8), but the impl builds it from "
                     "`rel + 1`, not provably equal to `rel`. If this verifies, "
                     "the fallback set is not grounded in the actual relation. "
                     "Probes `solveUnivariate rel = error cannotSolve`; "
                     "distinguishes `conditionOverReals (rel+1)` from "
                     "`conditionOverReals rel`.",
        "witness": _wit(
            ["h1 : solveUnivariate rel = Except.error SolveErr.cannotSolve"],
            ["h1"]),
    },

    # ---- L3: the other-failure propagation leg ----
    {
        "id": "weak-other-intercepted",
        "kind": "uniqueness",
        "expect": "reject",
        # Intercepts an `other` (non-cannot-solve) failure and turns it into the
        # condition-set fallback. Correct on L1 and L2; wrong exactly on the
        # `other` leg. Probes `solveUnivariate = error other`, the third outcome
        # no other rival exercises, so `solveUnivariate` is varied across all
        # three of its outcomes by the battery. No nagini counterpart: the sibling
        # carved the non-cannot-solve failures OUT of the domain by precondition
        # (solvability in {0,1}), so it had no case here; this carrier models the
        # `other` leg explicitly (it must propagate unchanged), so the rival is
        # ADDED for binder coverage (see the ADDED note in the accounting below).
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except SolveErr SetVal :=\n"
            "      match solveUnivariate rel with\n"
            "      | Except.ok h => Except.ok (SetVal.solverSet h)\n"
            "      | Except.error SolveErr.cannotSolve =>\n"
            "          Except.ok (SetVal.conditionOverReals rel)\n"
            "      | Except.error SolveErr.other =>\n"
            "          Except.ok (SetVal.conditionOverReals rel)"),
        "refinement": "a counterpart that intercepted a non-cannot-solve failure "
                      "and returned the condition-set fallback would suppress an "
                      "error that must always propagate unchanged. The unchanged "
                      "tests that expect such a failure to escape still fail (they "
                      "now see a returned set instead of the propagated failure). "
                      "It would NOT resolve.",
        "rationale": "REJECT from L3 (`solveUnivariate = error other -> out = "
                     "error other`): on an other-failure outcome the impl returns "
                     "the fallback where the post-image demands the failure "
                     "propagated unchanged. Probes `solveUnivariate rel = error "
                     "other`, the outcome no other rival exercises.",
        "witness": _wit(
            ["h1 : solveUnivariate rel = Except.error SolveErr.other"],
            ["h1"]),
    },
    {
        "id": "weak-other-relabelled",
        "kind": "uniqueness",
        "expect": "reject",
        # On the `other` leg it DOES propagate a failure (does not intercept, does
        # not return a set) but re-labels it as `cannotSolve`. Correct on L1, L2, and
        # on the ok/error dichotomy of L3; wrong only on WHICH failure escapes.
        # weak-other-intercepted attacks the error-vs-ok half of L3; nothing in the
        # battery pinned that the propagated failure keeps its own kind. Added by
        # audit for that clause.
        "module": _swap(
            _BASE, _IMPL,
            "    let result : Except SolveErr SetVal :=\n"
            "      match solveUnivariate rel with\n"
            "      | Except.ok h => Except.ok (SetVal.solverSet h)\n"
            "      | Except.error SolveErr.cannotSolve =>\n"
            "          Except.ok (SetVal.conditionOverReals rel)\n"
            "      | Except.error SolveErr.other => Except.error SolveErr.cannotSolve"),
        "refinement": "a counterpart that let a non-cannot-solve failure escape but "
                      "rewrote it into the cannot-solve shape would report the wrong "
                      "failure to the caller: code that distinguishes the two "
                      "failure shapes (including any caller that intercepts only "
                      "the cannot-solve one) would take the wrong branch, and the "
                      "unchanged tests that assert which failure escapes still fail. "
                      "It would NOT resolve.",
        "rationale": "REJECT from L3 (`solveUnivariate = error other -> out = error "
                     "other`): the impl propagates `error cannotSolve` where the "
                     "post-image demands `error other` — the failure escapes, but "
                     "not unchanged. If this verifies, L3 pins only THAT a failure "
                     "propagates and not WHICH, a clause weak-other-intercepted "
                     "(which attacks error-vs-ok) does not reach. Probes "
                     "`solveUnivariate rel = error other`.",
        "witness": _wit(
            ["h1 : solveUnivariate rel = Except.error SolveErr.other"],
            ["h1"]),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1
# soundness positive, 1 admissibility, 6 uniqueness rivals) + 2 AXIOM_TESTS;
# every one is accounted for below. This battery carries 10 (2 soundness
# positives, 1 admissibility, 7 uniqueness rivals). The two carriers are NOT the same
# partition: the sibling models a fractional-permission `Relation` object with a
# `solvability` tag in {0,1} and a try/except that turns a raised `SolverUndecided`
# into a fabricated fallback set, whereas this bundle models the whole routine's
# outcome over ONE opaque relation handle, observed only through the solver's
# three-way outcome and the condition set built from the relation. The nagini
# rivals are expressed over the tagged-object carrier; here they re-site onto the
# three disjoint legs of `asSetSpec`, so the mapping is stated case by case.
#
#   nagini case                                  -> here                          status
#   ---------------------------------------------------------------------------
#   pos-control-explicit-branch                  -> pos-arms-reordered            PORTED
#   (2nd structural positive, no sibling)        -> pos-error-kind-decided        ADDED
#   admiss-f2p-undecided-shaped   -> admiss-f2p-cannotsolve-nondegenerate         RE-AIMED
#   frame-mutate-readonly-solvability            -> (none, VACUOUS)               OMITTED
#   control-flow-no-handler-totality             -> weak-cannotsolve-escapes      RE-SITED
#   partial-domain-wrong-fallback-cond           -> weak-fallback-ungrounded      RE-SITED
#   uniqueness-fallback-not-flagged              -> weak-fallback-not-condition-set RE-SITED
#   partial-domain-fabricated-determined-fields  -> weak-success-alters-set       RE-SITED
#   partial-domain-branch-swap                   -> weak-success-returns-fallback RE-SITED
#   (other-leg propagation, no sibling)          -> weak-other-intercepted        ADDED
#   (other-leg error KIND, no sibling)           -> weak-other-relabelled         ADDED
#   ax-solve-univariate-soundness   (AXIOM_TESTS)-> (dropped, G-AX's job)         DROPPED
#   ax-solve-univariate-containment (AXIOM_TESTS)-> (dropped, G-AX's job)         DROPPED
#
# RE-SITED (the argument is unchanged; only the carrier is):
#  * control-flow-no-handler-totality attacked the sibling's TOTALITY obligation
#    (no Exsures declared, so a raised SolverUndecided must not escape). On this
#    carrier the totality failure IS the cannot-solve leg: the pre-patch returns
#    the solver result directly, so a cannot-solve report escapes as
#    `error cannotSolve` instead of becoming `ok (conditionOverReals rel)`. This
#    is exactly Solution_prepatch.lean — the canonical G-DIFF verify-not-resolve
#    rival — re-sited as weak-cannotsolve-escapes.
#  * partial-domain-wrong-fallback-cond attacked the sibling's fallback whose
#    defining condition was some OTHER token (rel.sym) rather than the relation
#    (rel.token). Here the fallback's defining relation IS the argument of
#    `conditionOverReals`; a rival building it from `rel + 1` is the faithful
#    re-siting of "the fallback set is defined by a different relation, not the
#    one passed in" (directive-8 grounding). weak-fallback-ungrounded.
#  * uniqueness-fallback-not-flagged attacked the sibling's is_fallback flag
#    (returning a genuine-solver-flavoured set with is_fallback == False on the
#    undecided tag). Here "genuine solver set vs symbolic fallback" IS the
#    `solverSet` vs `conditionOverReals` constructor distinction; a rival
#    returning `solverSet rel` on the cannot-solve leg is the faithful re-siting.
#    weak-fallback-not-condition-set.
#  * partial-domain-fabricated-determined-fields attacked the sibling's
#    determined branch rebuilding the solver's returned set with fabricated
#    fields. Here the success leg carries the solver's own opaque handle verbatim;
#    a rival perturbing that handle (`h + 1`) is the analogous "the solver's own
#    returned set is not preserved" attack. weak-success-alters-set.
#  * partial-domain-branch-swap attacked the sibling's INVERTED dichotomy
#    (fallback on the determined tag). Its success-leg half re-sites here as
#    returning `conditionOverReals rel` on the `ok` outcome:
#    weak-success-returns-fallback. An earlier revision of this port recorded the
#    case as OMITTED/"subsumed" by weak-success-alters-set +
#    weak-fallback-not-condition-set; the audit found that claim FALSE.
#    weak-success-alters-set perturbs the handle INSIDE `solverSet`, so it pins
#    only that constructor's ARGUMENT, and weak-fallback-not-condition-set lives
#    on the cannot-solve leg. Neither pins WHICH `SetVal` constructor the success
#    leg must emit, so the swap's success half was a genuinely unattacked clause,
#    not a redundant probe at a covered region.
#
# ADDED (3):
#  * pos-error-kind-decided — a second structurally-different correct impl that
#    collapses the two failure arms and recovers the distinction by DECIDING the
#    error kind (`if e = SolveErr.cannotSolve`), re-emitting `Except.error e`.
#    Chosen over a hoisted-`let` reshape because a `let` used once zeta-reduces:
#    that impl term is DEFINITIONALLY EQUAL to the frozen one (`rfl` closes it) and
#    the frozen tactic body closes it unretuned, so it would verify while testing
#    nothing. This impl term is NOT defeq to gold (`rfl` fails), so its retuned
#    proof genuinely re-establishes the obligation for a new impl shape.
#  * weak-other-intercepted — the sibling models `solvability` only in {0,1}
#    (determined/undecided) and carves every OTHER solver outcome OUT of the
#    domain by precondition, so it has no case for a non-cannot-solve failure.
#    This carrier distinguishes `cannotSolve` from `other` (solveUnivariate's
#    third outcome) and leg L3 pins that an `other` failure must propagate
#    unchanged; the rival attacks it. Added for BINDER COVERAGE: without it
#    `solveUnivariate` would only ever be probed at {ok, cannotSolve} and a rival
#    mishandling the `other` outcome would go uncaught. Not a fabricated
#    wrongness — it is a real divergence from L3 with a machine-checked witness
#    and a refinement argument (an error that must always escape would be
#    suppressed).
#  * weak-other-relabelled — the `other` leg's error KIND. weak-other-intercepted
#    attacks only the ok-vs-error half of L3 (return a set where a failure is due);
#    a rival that still fails but rewrites the failure into the cannot-solve shape
#    was unattacked, so L3 was pinned only as "a failure escapes" and not "THIS
#    failure escapes". Added by audit for that clause.
#
# RE-AIMED (admissibility): the sibling's admiss-f2p-undecided-shaped confirms the
#    precondition (n_free==1, solvability in {0,1}, half-permission on each field)
#    ACCEPTS an F2P-shaped input. This bundle has NO `require` clause (the admitted
#    domain is total) and no permission/field machinery, so that literal probe has
#    nothing to reject and cannot be ported as written. An earlier revision of this
#    port therefore recorded the case OMITTED, reasoning that `asSetSpec` is a total
#    function so `out = asSetSpec rel` is satisfiable at every `rel` by
#    construction. The audit found that reasoning INSUFFICIENT as a licence to drop
#    the lane: satisfiability-in-general is not the property the lane tests, which
#    is that the obligation is satisfiable AND non-degenerate at the F2P-SHAPED
#    input specifically — and nothing in the battery demonstrated that at the
#    cannot-solve leg. It is expressible here, so it is landed rather than argued
#    away: admiss-f2p-cannotsolve-nondegenerate discharges it by evaluation as an
#    in-region `assert` at that leg, before the frozen obligation closes verbatim,
#    and the audit machine-checked the assert LIVE (three false variants of the
#    claim each leave `case «admiss_1: ...»` unsolved at exit 1; the shipped claim
#    verifies at exit 0).
#
# OMITTED (1):
#  * frame-mutate-readonly-solvability. Nagini-specific (fractional heap
#    permissions; the sibling's `rel.solvability = 1` write under a
#    half-permission). This backend is referentially transparent and the method
#    declares no `mut` binder: `rel` is an immutable value with no heap and no
#    aliasing, so there is no read-only input to overwrite and no substitute
#    probe. VACUOUS; no substitute fabricated.
#
# BINDER / CLAUSE COVERAGE. The sole input `rel` is observed only through
# `solveUnivariate rel` (three outcomes) and `conditionOverReals rel` (one
# grounded set). The reject rivals probe `solveUnivariate` at all three outcomes
# {ok, cannotSolve, other} — so the input's observation is never pinned across
# the battery — and weak-fallback-ungrounded additionally moves the
# `conditionOverReals` argument off `rel`, exercising the fallback's dependence on
# the input. Every top-level leg of `asSetSpec` (L1-L3) is attacked, and on each
# leg BOTH the constructor and its argument are pinned separately:
#   L1 two ways — constructor by weak-success-returns-fallback (`conditionOverReals`
#      where `solverSet` is due), argument by weak-success-alters-set (`h + 1`);
#   L2 three ways — ok-vs-error by weak-cannotsolve-escapes, constructor by
#      weak-fallback-not-condition-set, grounding of the argument by
#      weak-fallback-ungrounded;
#   L3 two ways — ok-vs-error by weak-other-intercepted, error KIND by
#      weak-other-relabelled.
# Both positive controls defend the whole obligation, and each is a reshape the
# carrier can distinguish from gold: `pos-arms-reordered` and
# `pos-error-kind-decided` both produce impl terms that are NOT definitionally
# equal to the frozen one (`rfl` fails on each), so neither passes by restating
# what the frozen file already establishes.
#
# WITNESS DISCRIMINATION (verified during authoring, and re-checked by the gate's
# two builds per reject case): each witness elaborates against its rival (the
# rival's output provably differs from `asSetSpec rel` on the hypothesised region)
# and FAILS against the frozen solution (the frozen impl reduces the same goal to
# `False` with only a single satisfiable outcome hypothesis in context, so nothing
# closes it). The opaque carrier forbids a `decide`-on-a-literal witness —
# `solveUnivariate` never reduces at a concrete `rel` — so every witness
# hypothesises the solver outcome at a symbolic `rel`; each carries exactly ONE
# hypothesis (jointly satisfiable by construction, no contradictory pair), an
# ordinary equality of the opaque observation rather than an assumption of the
# conclusion, and no `sorry`/`admit`/`native_decide`/`axiom` appears.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# `axiom` (the unchanged solver is `opaque` with no asserted `ensures`), so there
# is nothing there to probe.
AXIOM_TESTS = []
