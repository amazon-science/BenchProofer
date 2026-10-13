"""properties.py — G-PBT falsification battery for django__django-13925 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct implicitPrimaryKeyAdvisory`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness ELABORATES against the rival and FAILS
against the frozen solution).

DEFENDED SURFACE (one contracted self-diagnostic that decides whether to emit
an advisory about an auto-created primary key when no key type was chosen):

  implicitPrimaryKeyAdvisory
      (pkAutoCreated : Bool) (pkInheritedFromAncestor : Bool)
      (defaultKeyTypeConfigured : Bool) (appKeyTypeConfigured : Bool)
      return (out : Bool)
    ensures out =
      (pkAutoCreated && !pkInheritedFromAncestor &&
       !defaultKeyTypeConfigured && !appKeyTypeConfigured)   -- the only clause

The whole postcondition is a single boolean equality: the advisory fires
(``out = true``) EXACTLY on the conjunction of four read-only observations —
the key was auto-supplied, is NOT the implicit key inherited from an ancestor,
and no default key type is configured project-wide OR for the model's own
application. On concrete boolean inputs the clause reduces to a comparison
``decide`` computes, so no rival can "echo an opaque oracle": there is no
axiomatized answer-key (the ``axioms`` region is empty), every operand is a
transparent ``Bool`` argument, and the only way to satisfy the clause is to
compute exactly this conjunction (directive 8, grounded).

WHAT THE SPEC DEFENDS. The load-bearing content of the fix is the second
conjunct ``!pkInheritedFromAncestor``: the advisory must be SUPPRESSED when the
model's only auto-created primary key is the implicit key it holds by virtue of
inheriting from an ancestor (a parent-link one-to-one relation), because the
ancestor is where that choice belongs and is diagnosed on its own. The other
three conjuncts (auto-created gate, project-wide default, application default)
are the pre-existing suppression conditions; the whole-equality pins all four so
no wrong impl of the modeled decision can satisfy it.

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on ALL FOUR inputs, and each is the sole conjunct a distinct rival
mishandles:

  * ``pkInheritedFromAncestor`` — the fix's own conjunct. A rival that drops it
    is correct everywhere EXCEPT the inherited-ancestor sub-domain and is refuted
    at ``pkInheritedFromAncestor = true`` (with the other suppressors off).
  * ``pkAutoCreated`` — the outer gate. A rival that ignores it warns on a model
    whose key was NOT auto-supplied and is refuted at ``pkAutoCreated = false``.
  * ``defaultKeyTypeConfigured`` — the project-wide suppressor. A rival that
    drops it warns when a project-wide default IS set; refuted at
    ``defaultKeyTypeConfigured = true``.
  * ``appKeyTypeConfigured`` — the application suppressor. A rival that drops it
    warns when the app configures a default; refuted at
    ``appKeyTypeConfigured = true``.

Each binder is therefore held at BOTH truth values across the reject witnesses,
so none is pinned at a single value that a rival could quietly abuse.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION (nagini ``weak-frame-mutate``) — VACUOUS. The nagini sibling
    carries it because its record input is held at a fractional heap permission
    (``Acc(.,1/2)``) that a wrong impl can illegally overwrite. Velvet is
    referentially transparent: every input here is an immutable ``Bool`` value,
    there is no ``mut`` binder, no heap and no aliasing — there is no read-only
    input to mutate and no substitute probe to build. Not fabricated (porting
    map: vacuous here).
  * ADMISSIBILITY (nagini ``admiss-self-call``) — APPLIES, and is LANDED
    (``admiss-f2p-nondegenerate``). This bundle declares NO ``require`` clause
    (the pre-conditions region is empty), so the nagini probe's own question ("is
    the half-permission Requires establishable for a freshly built record?") has
    nothing to admit. That is NOT a reason to drop the lane. The analogue on a
    total carrier is the obligation being UNSATISFIABLE or DEGENERATE at exactly
    an F2P-shaped input — a spec no impl can meet, or one that collapses the
    interesting inputs to a single constant answer, reads from the outside
    exactly like a spec every impl meets. A positive that discharges the
    post-image AT those concrete inputs, by evaluation, as an in-region
    ``assert``, before closing the frozen obligation verbatim, tests that
    directly. An earlier revision of this file recorded the lane as vacuous on
    the ground that "an admissibility assert would reduce to a trivial
    tautology". That was measured WRONG: the assert is live (falsify any one of
    its clauses and the build leaves ``unsolved goals`` naming the ``adm``
    prefix, EXIT 1, while the honest form is EXIT 0), and a transparent
    post-image is precisely what makes the SATISFIABILITY and NON-COLLAPSE of
    the five harness-shaped points machine-checkable rather than argued. See the
    case.
  * COUNT-OUT-OF-RANGE (nagini ``weak-count-out-of-range``) — NO COUNTERPART.
    The nagini surface returns an ``int`` count and its clause (V) pins that
    count to a bit (0 or 1), so a rival returning 2 is meaningful there. This
    carrier models the single observable as a ``Bool`` (mapping.md §2: the
    returned list is a one-element advisory iff the guard holds, else empty), so
    the "count is a bit" facet is STRUCTURALLY guaranteed by the type — there is
    no out-of-range value a ``Bool`` rival can return. Reported as an omission,
    not faked.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent boolean
    conjunction of the four method inputs, not an axiomatized oracle; the
    ``axioms`` region is empty. The echo positive below is an honest cheapest
    correct control, not a wrong echo.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line a single ``return`` over immutable values,
    no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
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
  * AXIOM lane (nagini's A-reference deep-model over the 2**5 truth table) —
    DROPPED. The axiom lane is G-AX's job; this gate ignores ``AXIOM_TESTS``
    regardless. (mapping.md §3: this bundle declares no axiom, G-AX skip.)

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``implicitPrimaryKeyAdvisoryTester b1 b2 b3 b4 = false`` says the extracted
program's result violates the postcondition at that concrete boolean input. It
is checked in a file whose ``prove_correct`` block has been stripped (so no
tactic script can mask the verdict) and there are no ``require`` clauses, so
every input reaches the postcondition. The four inputs are concrete ``Bool``
literals, so ``decide`` settles the whole equality — no opaque term, no
conditioning, no head binders (hence no consistency obligation). Each witness
was confirmed with two real builds to ELABORATE against its rival and FAIL
against the frozen solution.

WITNESS NON-FORGERY (measured, not argued). Each gold-side failure here is a
plain kernel EVALUATION of the concrete claim —
``Tactic `decide` proved that the proposition
implicitPrimaryKeyAdvisoryTester <bits> = false is false`` — so the exit code is
carrying the truth of the claim and nothing else. Confirmed by the flipped-claim
experiment on all four reject cases: rebuilding a file that differs from the
witness ONLY in asserting ``= true`` instead of ``= false`` SWAPS both exit codes
(gold 0, rival 1, with the mirror-image ``… = true is false`` error on the rival),
where a hollow witness would have failed identically on both. The gold-side error
therefore tracks the claim, and no case rests on a syntactic accident, a missing
identifier, a stuck reduction, or a timeout.
"""
from pathlib import Path

INSTANCE = "django__django-13925"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The COMPLETE frozen guard-return expression; lies
# ---- wholly inside the single `-- impl-start`/`-- impl-end` region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap). Anchoring
# ---- on the whole expression keeps every surgery inside the elided region — the
# ---- frozen spec (the `method` header and the `ensures` clause, which also
# ---- spells out the conjunction) is never touched. ----
_IMPL = (
    "    return (pkAutoCreated && !pkInheritedFromAncestor &&\n"
    "            !defaultKeyTypeConfigured && !appKeyTypeConfigured)"
)

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body: str) -> str:
    """Full Solution.lean variant with ONLY the impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble: reach the contract through Velvet's tester machinery.
# ---- The method takes four `Bool` arguments, so its extracted tester is
# ---- `implicitPrimaryKeyAdvisoryTester : Bool -> Bool -> Bool -> Bool -> Bool`;
# ---- `... = false` at a concrete tuple says the extracted program's result
# ---- violates the postcondition there. Checked in a file whose `prove_correct`
# ---- block has been stripped, so no tactic script can mask the verdict. ----
_TESTER = (
    "extract_program_for implicitPrimaryKeyAdvisory\n"
    "prove_precondition_decidable_for implicitPrimaryKeyAdvisory\n"
    "prove_postcondition_decidable_for implicitPrimaryKeyAdvisory\n"
    "derive_tester_for implicitPrimaryKeyAdvisory\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. The post-image is a point-wise
    # boolean equality (no induction), so each reproof stays within the frozen
    # `loom_solve` script. Both verified out-of-band with a real build against
    # the frozen spec.
    # =====================================================================
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: invert the guard into an explicit if/then/else that returns
        # `true` on the warranted branch and `false` otherwise. Same truth
        # function as the direct conjunction; a structurally-different but correct
        # impl. Ports the nagini structural positive (`pos-control-reorder`).
        "module": _impl(
            "    if pkAutoCreated && !pkInheritedFromAncestor &&\n"
            "       !defaultKeyTypeConfigured && !appKeyTypeConfigured then\n"
            "      return true\n"
            "    else\n"
            "      return false"),
        "rationale": "a correct but reshaped impl (explicit if/then/else over the "
                     "same four-way conjunction, true on the warranted branch and "
                     "false otherwise) computes the same advisory bit, so the sole "
                     "clause `out = (pkAutoCreated && !pkInheritedFromAncestor && "
                     "!defaultKeyTypeConfigured && !appKeyTypeConfigured)` still "
                     "discharges. If it fails to verify the spec is over-fit to one "
                     "syntactic shape => SPEC-TOO-STRONG. Verified out-of-band.",
    },
    {
        "id": "pos-cheapest-grounded",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest control: bind the grounded conjunction to a typed local
        # and return it. Because the post-image is a transparent conjunction of
        # the four inputs (not an opaque oracle), this still does the real work;
        # there is no wrong echo that could verify. Ports the nagini grounded
        # cheapest control (`pos-cheapest-grounded`).
        "module": _impl(
            "    let warranted : Bool :=\n"
            "      pkAutoCreated && !pkInheritedFromAncestor &&\n"
            "      !defaultKeyTypeConfigured && !appKeyTypeConfigured\n"
            "    return warranted"),
        "rationale": "the cheapest correct impl binds the grounded conjunction to a "
                     "typed local and returns it. Because the post-image is a "
                     "spelled-out boolean function of the four inputs — not an "
                     "axiomatized answer key — this still performs the real "
                     "decision; there is no wrong echo that could verify (grounded "
                     "oracle, directive 8). Demonstrates the spec is NOT "
                     "echo-vulnerable. Must verify; verified out-of-band.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). No `require` clause exists here,
    # so "a normal input satisfies the precondition" is vacuously true and is NOT
    # what this case tests. The total-carrier analogue is that the obligation is
    # UNSATISFIABLE or DEGENERATE at a harness-shaped input. This case discharges
    # the post-image AT the five harness-shaped points as an in-region `assert`,
    # keeping the frozen return and the frozen `loom_solve` so the method's own
    # obligation still closes and the assert is LIVE.
    # =====================================================================
    {
        "id": "admiss-f2p-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The five points the failing/regression tests actually drive, plus the
        # NON-COLLAPSE of the two that differ only in the fix's own conjunct:
        #   * inherited-ancestor key, no defaults      -> false (suppressed);
        #   * plain auto-created key, no defaults      -> true  (the advisory);
        #   * explicitly declared key                  -> false;
        #   * app configures a default key type        -> false;
        #   * project-wide default key type configured -> false;
        #   * and the first two DISAGREE, so the obligation does not degenerate
        #     to one constant answer over the sub-domain the fix distinguishes.
        "module": _impl(
            "    assert (with_name_prefix `adm\n"
            "      ((true && !true && !false && !false) = false ∧\n"
            "       (true && !false && !false && !false) = true ∧\n"
            "       (false && !false && !false && !false) = false ∧\n"
            "       (true && !false && !false && !true) = false ∧\n"
            "       (true && !false && !true && !false) = false ∧\n"
            "       (true && !true && !false && !false) ≠\n"
            "         (true && !false && !false && !false)))\n"
            + _IMPL),
        "rationale": "the sole clause is SATISFIABLE and NON-DEGENERATE at exactly "
                     "the harness-shaped inputs. The advisory is pinned false on "
                     "the inherited-ancestor key, true on the plain auto-created "
                     "key, and false on each of the three suppressed "
                     "configurations (explicit key, application default, "
                     "project-wide default); and the first two answers DIFFER, so "
                     "the obligation does not collapse the sub-domain the fix "
                     "distinguishes to a single constant. The assert is LIVE, not "
                     "decorative: replacing any one clause with a false one (e.g. "
                     "`(true && !true && !false && !false) = true`, or the "
                     "disequality flipped to an equality) leaves `unsolved goals` "
                     "naming the `adm` prefix (EXIT 1), while the honest form is "
                     "EXIT 0 — both measured out-of-band with real builds. The "
                     "impl and the proof script are the frozen ones, so the "
                     "`prove_correct` obligation still discharges on its own. If "
                     "the assert FAILS => PRECOND-TOO-STRONG (a degenerate or "
                     "unsatisfiable obligation at an input the harness actually "
                     "drives). (Sibling: admiss-self-call, re-aimed at the "
                     "total-carrier analogue since there is no `require` to admit.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete boolean input (ELABORATES against the rival, FAILS against gold —
    # both halves confirmed out-of-band with real builds) and the refinement
    # argument for why its faithful real counterpart would NOT resolve.
    # =====================================================================
    {
        "id": "weak-drop-inherited-suppression",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug (the pre-patch guard): drop the `!pkInheritedFromAncestor`
        # conjunct, so the advisory fires whenever the key is auto-created and no
        # default type is configured. Correct on every model whose auto key is NOT
        # the inherited ancestor key; WRONG on exactly the inherited-ancestor
        # sub-domain — the sub-domain the failing test exercises.
        "module": _impl(
            "    return (pkAutoCreated && !defaultKeyTypeConfigured &&\n"
            "            !appKeyTypeConfigured)"),
        "refinement": "this is the PRE-PATCH decision: it omits the suppression for "
                      "the implicit key a model holds purely by inheriting from an "
                      "ancestor. On a model whose only auto-created key is that "
                      "inherited ancestor key it emits the advisory where the fixed "
                      "behaviour suppresses it. The failing tests assert NO advisory "
                      "for exactly such an inherited model, so the faithful real "
                      "counterpart still emits it and would NOT resolve — this is the "
                      "exact defect the fix corrects.",
        "rationale": "REJECT from the sole clause: at "
                     "(pkAutoCreated, pkInheritedFromAncestor, "
                     "defaultKeyTypeConfigured, appKeyTypeConfigured) = "
                     "(true, true, false, false) the post-image is false "
                     "(!pkInheritedFromAncestor is false) yet this impl returns true. "
                     "Correct everywhere the key is not the inherited ancestor key; "
                     "wrong on exactly that sub-domain. Refuted at "
                     "(true, true, false, false) — the fix's own conjunct. If it "
                     "verified => SPEC-TOO-WEAK (the reported bug would go "
                     "unnoticed).",
        "witness": _witness(
            "implicitPrimaryKeyAdvisoryTester true true false false"),
    },
    {
        "id": "weak-ignore-app-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the application-default suppressor: warn even when the model's own
        # application configures a default key type. Correct whenever that app
        # default is unset; wrong only when it IS set — the sub-domain a P2P test
        # exercises. Carries the appKeyTypeConfigured = true point so that binder
        # is not pinned at false.
        "module": _impl(
            "    return (pkAutoCreated && !pkInheritedFromAncestor &&\n"
            "            !defaultKeyTypeConfigured)"),
        "refinement": "this drops the suppression when the model's own application "
                      "configures a default key type. When the app sets that default "
                      "the advisory must be suppressed; this still emits it. A "
                      "P2P/regression test asserts NO advisory when the application "
                      "overrides the default, so the faithful real counterpart warns "
                      "spuriously and would NOT resolve.",
        "rationale": "REJECT from the sole clause: at "
                     "(pkAutoCreated, pkInheritedFromAncestor, "
                     "defaultKeyTypeConfigured, appKeyTypeConfigured) = "
                     "(true, false, false, true) the post-image is false "
                     "(!appKeyTypeConfigured is false) yet this impl returns true. "
                     "Pins the appKeyTypeConfigured = true sub-domain no other rival "
                     "probes. Refuted at (true, false, false, true). If it verified "
                     "=> SPEC-TOO-WEAK (the application-default suppressor would be "
                     "unpinned).",
        "witness": _witness(
            "implicitPrimaryKeyAdvisoryTester true false false true"),
    },
    {
        "id": "weak-ignore-project-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the project-wide-default suppressor: warn even when a project-wide
        # default key type is configured. Correct whenever that default is unset;
        # wrong only when it IS set. Carries the defaultKeyTypeConfigured = true
        # point so that binder is not pinned at false.
        "module": _impl(
            "    return (pkAutoCreated && !pkInheritedFromAncestor &&\n"
            "            !appKeyTypeConfigured)"),
        "refinement": "this drops the suppression when a project-wide default key "
                      "type is configured. When that default is set the advisory "
                      "must be suppressed; this still emits it. A P2P/regression test "
                      "asserts NO advisory when the project-wide default is "
                      "configured, so the faithful real counterpart warns spuriously "
                      "and would NOT resolve.",
        "rationale": "REJECT from the sole clause: at "
                     "(pkAutoCreated, pkInheritedFromAncestor, "
                     "defaultKeyTypeConfigured, appKeyTypeConfigured) = "
                     "(true, false, true, false) the post-image is false "
                     "(!defaultKeyTypeConfigured is false) yet this impl returns "
                     "true. Pins the defaultKeyTypeConfigured = true sub-domain no "
                     "other rival probes. Refuted at (true, false, true, false). If "
                     "it verified => SPEC-TOO-WEAK (the project-wide suppressor would "
                     "be unpinned).",
        "witness": _witness(
            "implicitPrimaryKeyAdvisoryTester true false true false"),
    },
    {
        "id": "weak-ignore-auto-created-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the outer auto-created gate: emit the advisory even for a model
        # whose primary key was NOT auto-supplied (an explicitly declared key).
        # Correct whenever the key IS auto-created; wrong on the explicit-key
        # sub-domain. Carries the pkAutoCreated = false point so that binder is
        # not pinned at true.
        "module": _impl(
            "    return (!pkInheritedFromAncestor && !defaultKeyTypeConfigured &&\n"
            "            !appKeyTypeConfigured)"),
        "refinement": "this drops the auto-created gate, so a model whose primary key "
                      "was explicitly declared (not auto-supplied) would still draw "
                      "the advisory. A P2P/regression test asserts NO advisory for a "
                      "model with an explicitly declared key, so the faithful real "
                      "counterpart warns spuriously on such models and would NOT "
                      "resolve.",
        "rationale": "REJECT from the sole clause: at "
                     "(pkAutoCreated, pkInheritedFromAncestor, "
                     "defaultKeyTypeConfigured, appKeyTypeConfigured) = "
                     "(false, false, false, false) the post-image is false "
                     "(pkAutoCreated is false) yet this impl returns true. Pins the "
                     "pkAutoCreated = false sub-domain no other rival probes. Refuted "
                     "at (false, false, false, false). If it verified => "
                     "SPEC-TOO-WEAK (the auto-created gate would be unpinned).",
        "witness": _witness(
            "implicitPrimaryKeyAdvisoryTester false false false false"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. This battery carries 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals). The nagini sibling has 8 SPEC
# cases (2 soundness positives, 1 admissibility, 5 uniqueness rivals;
# AXIOM_TESTS empty) over
# `check_default_pk(pk: PkField, setting_overridden, appconfig_overridden) -> int`,
# whose postcondition has TWO clauses: (V) the count is a bit (0 or 1) and (W)
# the load-bearing equivalence `(Result()==1) == advisory_warranted(...)` over
# five booleans (pk.auto, two ancestor-reuse sub-flags ra/rb, and the two
# override params). THIS bundle models the SAME functional core as a single
# `Bool`-valued decision, with two carrier narrowings recorded in mapping.md:
#   * the nagini pair of sub-flags (ra, rb) whose CONJUNCTION `ra and rb` is the
#     "reuses the ancestor's declared key" condition is folded into ONE boolean
#     `pkInheritedFromAncestor` (mapping.md §2: the whole `isinstance(...) and
#     ...parent_link` sub-expression is a single boolean), so the two nagini
#     rivals that attacked ra vs the ra/rb conjunction (`weak-drop-reuse-
#     suppression`, `weak-suppress-on-A-only`) collapse to ONE rival here
#     (`weak-drop-inherited-suppression`) — there is no separable A-only
#     sub-domain on this carrier;
#   * the nagini `int` count is folded into the `Bool` `out` (mapping.md §2: the
#     advisory is present iff the guard holds), so clause (V) is structural and
#     the nagini `weak-count-out-of-range` (return 2) has NO expressible
#     counterpart.
#
#   nagini case                    -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder            -> pos-control-reorder            RE-EXPRESSED
#   pos-cheapest-grounded          -> pos-cheapest-grounded          PORTED
#   admiss-self-call               -> admiss-f2p-nondegenerate       RE-AIMED (total-carrier analogue)
#   weak-frame-mutate              -> (none)                         VACUOUS (no heap)
#   weak-drop-reuse-suppression    -> weak-drop-inherited-suppression PORTED (the bug)
#   weak-suppress-on-A-only        -> (folds into the above)         NO COUNTERPART (carrier folds ra/rb)
#   weak-ignore-appconfig-override -> weak-ignore-app-default        PORTED
#   weak-count-out-of-range        -> (none)                         NO COUNTERPART (Bool carrier)
#   (added, no nagini counterpart) -> weak-ignore-project-default    ADDED (project-wide suppressor)
#   (added, no nagini counterpart) -> weak-ignore-auto-created-gate  ADDED (auto-created gate)
#   AXIOM_TESTS ([])               -> (none)                         DROPPED (G-AX lane)
#
# RE-EXPRESSED (pos-control-reorder): the nagini positive used per-conjunct
#   early-out returns (return 0 on each failing conjunct, fall-through 1). Here
#   the equivalent structural difference inverts the guard into one explicit
#   if/then/else returning true/false — a different source shape, same truth
#   function. Verified out-of-band.
# PORTED (pos-cheapest-grounded): nagini binds the grounded predicate to a typed
#   local and returns 1/0 from it. Here the analogue binds the grounded boolean
#   conjunction to a typed local and returns it; the same no-echo argument holds
#   (the post-image is a transparent conjunction, not an opaque oracle).
# RE-AIMED (admissibility): the nagini self-call control probed that the
#   Acc(...,1/2) Requires is establishable for harness-shaped records — a
#   permission obligation that does not exist on this carrier, since no `require`
#   clause is declared. An earlier revision therefore recorded the whole lane as
#   VACUOUS. That was wrong, and measured wrong: the total-carrier analogue of
#   PRECOND-TOO-STRONG is the obligation being unsatisfiable or DEGENERATE at a
#   harness-shaped input, which `admiss-f2p-nondegenerate` tests by discharging
#   the post-image at the five driven points (and their non-collapse) as an
#   in-region assert, ahead of the byte-identical frozen obligation. The assert
#   verifies (EXIT 0) and is live (any clause falsified => `unsolved goals` on the
#   `adm` prefix, EXIT 1), so the lane is expressible here, not vacuous.
# VACUOUS (weak-frame-mutate): this backend is referentially transparent, declares
#   no `mut` binder, and has no heap — the nagini rival overwrites a record field
#   held at half permission, which on this carrier is an immutable `Bool` value.
#   No read-only field to overwrite and no substitute probe. Not fabricated
#   (porting map: vacuous here).
# PORTED (weak-drop-inherited-suppression): the nagini `weak-drop-reuse-suppression`
#   is the pre-patch guard that omits the ancestor-reuse suppression conjunct;
#   here dropping `!pkInheritedFromAncestor` is the identical defect, refuted at
#   the inherited-ancestor point (true, true, false, false). This is THE bug the
#   F2P tests demand fixed.
# NO COUNTERPART (weak-suppress-on-A-only): the nagini rival suppresses on the
#   `isinstance` sub-flag ra ALONE (dropping the conjunction with rb), wrong on
#   the (ra, rb) = (true, false) sub-domain. mapping.md §2 folds that whole
#   sub-expression into the single boolean `pkInheritedFromAncestor`, so there is
#   no separable A-only sub-domain on this carrier — the distinction the nagini
#   rival abused is not modeled here (a plain one-to-one PK without parent_link
#   simply sets pkInheritedFromAncestor = false). Omitted because the modeled
#   surface does not include that split, NOT because it was hard to prove.
# PORTED (weak-ignore-app-default): the nagini `weak-ignore-appconfig-override`
#   drops the application-default suppressor; ported directly, refuted at
#   (true, false, false, true).
# NO COUNTERPART (weak-count-out-of-range): the nagini rival returns count 2 to
#   violate clause (V) "the count is a bit". This carrier models the observable
#   as a `Bool` (mapping.md §2), so (V) is guaranteed by the type and there is no
#   out-of-range value a `Bool` rival can return. Omitted as a carrier fact.
# ADDED (2, no nagini counterpart): the nagini battery left the project-wide
#   default suppressor (`setting_overridden` / `not settings.is_overridden(...)`)
#   and the auto-created gate (`pk.auto`) unattacked by a dedicated rival. This
#   carrier's whole-equality post-image makes both directly refutable, so
#   weak-ignore-project-default (refuted at true, false, true, false) and
#   weak-ignore-auto-created-gate (refuted at false, false, false, false) attack
#   those two remaining conjuncts. Both are real divergences with machine-checked
#   witnesses, added so EVERY conjunct of the sole clause has a dedicated rival
#   and every binder is varied across both truth values.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line a single ``return`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
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
# BINDER / CLAUSE / POINT COVERAGE. The sole clause is a four-way conjunction;
#   each conjunct is the unique operand one reject rival mishandles, so all four
#   are attacked. The four reject witnesses probe FOUR distinct input tuples:
#     weak-drop-inherited-suppression  (true,  true,  false, false)
#     weak-ignore-app-default          (true,  false, false, true )
#     weak-ignore-project-default      (true,  false, true,  false)
#     weak-ignore-auto-created-gate    (false, false, false, false)
#   Across them pkAutoCreated takes {true, false}; pkInheritedFromAncestor takes
#   {true, false}; defaultKeyTypeConfigured takes {true, false};
#   appKeyTypeConfigured takes {true, false}. Every input binder is varied across
#   both truth values, so no binder is pinned at one value (pts=4). Every witness
#   was confirmed with two real builds to ELABORATE against the rival and FAIL
#   against the frozen solution.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (every guard operand is a direct boolean observation, mapping.md §3,
# G-AX skip), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
