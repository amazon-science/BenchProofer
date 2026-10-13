"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7236 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside an ``-- impl-start`` / ``-- impl-end`` region — which
the consumer spec view elides, so ``markers.same_spec`` holds and every
``prove_correct <name>`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (two contracted methods, both purely-functional boolean cores):

  markedSkipped (skipMarked : Bool) return (out : Bool)
    ensures out = skipMarked                                        -- (M) identity

  teardownPostponed (asyncTest debuggerActive skipMarked : Bool) return (postpone : Bool)
    ensures postpone = (!asyncTest && debuggerActive && !skipMarked)  -- (T) biconditional

``teardownPostponed`` calls ``markedSkipped`` as a sub-method
(callee-under-spec); the caller's proof applies the generated
``markedSkipped_correct`` directly. There is NO ``require`` clause on either
method and the ``axioms`` region is EMPTY — both post-images are grounded in the
methods' own boolean inputs (no opaque answer-key to echo).

The load-bearing clause (T) is a complete BICONDITIONAL over THREE distinct
read-only boolean inputs. Any impl whose decision diverges from
``!asyncTest && debuggerActive && !skipMarked`` on ANY point of the boolean cube
is rejected. The three input binders are the sub-inputs the reject witnesses
vary:
  * ``skipMarked`` — the decision must exclude a mark-bearing test (the headline
    behaviour under repair);
  * ``debuggerActive`` — the deferral applies only under the interactive
    post-mortem debugger;
  * ``asyncTest`` — the deferral never applies to an asynchronous test (its
    teardown is driven by its own framework, on a code path the guard never
    reaches).

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling carries TWO MANDATORY
    permission rivals (a write into a read-only half-permission input:
    ``postmortem_mode`` and ``skip_marker``). Lean and Velvet are referentially
    transparent: every input is an immutable ``Bool`` value, this bundle
    declares NO ``mut`` binder over any input, and there is no heap or aliasing —
    so there is no read-only input to overwrite and no permission system to trip.
    Not fabricated (porting map: vacuous here).
  * DIVERGENCE / NON-TERMINATION: INAPPLICABLE as a shipped reject case, and
    closed by the verifier rather than vacuous. Each frozen impl is a closed
    boolean expression with no loop, so there is no loop in the frozen body to
    make spin and this bundle ships no divergence rival; but "a diverging impl
    cannot be written" is withdrawn, since a rival rewrites the whole impl region
    and may splice a loop. Under this bundle's
    ``set_option loom.semantics.termination "total"`` a postcondition is claimed of
    ALL runs, not only terminating ones, so the verifier demands a decreasing
    measure on every loop AND discharges its descent; the option cannot drift from
    the file's ``open TotalCorrectness DemonicChoice``, because the ``set_option``
    elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with the proof
    reduced to a bare ``loom_solve``: a spliced
    ``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z`` with body
    ``z := z + 1`` is REJECTED on the measure's own goal,
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``.
  * PARTIAL-DOMAIN / VALUE — APPLIES; the whole reject lane. Each rival is
    CORRECT on most of the (async × debugger × skip) cube but diverges on a named
    sub-domain, refuted by the biconditional (T) — or, for the sub-method, by
    the identity (M).
  * UNGROUNDED-ORACLE ECHO — N/A. Both post-images are closed boolean
    expressions over the methods' own inputs (empty ``axioms`` region); the
    cheapest correct impl simply evaluates the expression, covered by the
    positive controls.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery
(``<name>Tester <inputs> = false`` says the extracted program's result violates
the method's postcondition at that concrete input), checked in a file whose
``prove_correct`` blocks are stripped so no tactic script can mask the verdict.
Both fields/inputs are ``Bool``, so postcondition decidability derives and each
witness closes by ``decide``. Every witness was checked out-of-band with
``scripts/lean_verify.sh``: each ELABORATES against its rival (the tester
``decide``s to ``false`` — the rival's output violates the postcondition at the
probed point) and FAILS against the frozen solution (whose tester ``decide``s to
``true`` — the spec holds there). No witness binds a hypothesis (the carrier is
fully transparent — every input is a ``Bool`` literal), so there is no
joint-satisfiability obligation. Every reject case's two builds were
independently RE-DERIVED by an adversarial audit, which also read each gold-side
failure to confirm it is a semantic refutation (`decide` proved the claim false)
rather than a stuck reduction or a missing identifier, and confirmed gold's
tester is `true` at every point of the boolean cube.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references
(mapping.md §3: G-AX is ``skip``). Nothing in either proof rests on an axiom, and
this gate ignores ``AXIOM_TESTS`` regardless. See the accounting block at the
bottom for the full nagini→velvet disposition table.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7236"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies WHOLLY inside a single method's impl region and is
# unique in Solution.lean, so every swap edits only the implementation.
# ---------------------------------------------------------------------------

# The whole `teardownPostponed` impl body (three lines between its markers).
_TD_IMPL = (
    "    let skipped ← markedSkipped skipMarked\n"
    "    let decision := !asyncTest && debuggerActive && !skipped\n"
    "    return decision")
assert _BASE.count(_TD_IMPL) == 1, "teardownPostponed impl region drifted"

# The whole `markedSkipped` impl region (markers + single return).
_MS_IMPL = (
    "    -- impl-start\n"
    "    return skipMarked\n"
    "    -- impl-end")
assert _BASE.count(_MS_IMPL) == 1, "markedSkipped impl region drifted"


def _td(body):
    """Solution.lean with the teardownPostponed impl body replaced."""
    return _swap(_BASE, _TD_IMPL, body)


def _td_rival(expr):
    """teardownPostponed impl reduced to a single grounded decision expr."""
    return _td(f"    let decision := {expr}\n    return decision")


def _ms(body):
    """Solution.lean with the markedSkipped impl region replaced (markers kept)."""
    return _swap(_BASE, _MS_IMPL,
                 "    -- impl-start\n" + body + "\n    -- impl-end")


# ---- witness preambles. Reach each method's contract through Velvet's tester.
def _td_tester(body):
    return ("extract_program_for teardownPostponed\n"
            "prove_precondition_decidable_for teardownPostponed\n"
            "prove_postcondition_decidable_for teardownPostponed\n"
            "derive_tester_for teardownPostponed\n\n" + body)


def _ms_tester(body):
    return ("extract_program_for markedSkipped\n"
            "prove_precondition_decidable_for markedSkipped\n"
            "prove_postcondition_decidable_for markedSkipped\n"
            "derive_tester_for markedSkipped\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally-different CORRECT impls that
    # MUST verify, else SPEC-TOO-STRONG. Each keeps the frozen `prove_correct
    # ... by loom_solve` proof body; all three were confirmed to build.
    # =====================================================================
    {
        "id": "pos-td-direct",
        "kind": "soundness",
        "expect": "verify",
        # Drop the intermediate `skipped` sub-call and the `decision` local:
        # return the grounded boolean expression directly. Observationally
        # identical; the sub-method call is inlined as the identity on skipMarked.
        "module": _td_rival("!asyncTest && debuggerActive && !skipMarked"),
        "rationale": "structurally-different CORRECT impl of teardownPostponed: the "
        "decision boolean `!asyncTest && debuggerActive && !skipMarked` is returned "
        "directly (no sub-call, no intermediate local). It is GROUNDED in the "
        "method's own inputs, so returning it is the honest cheapest impl and MUST "
        "verify against the biconditional (T), else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-td-ifelse",
        "kind": "soundness",
        "expect": "verify",
        # Explicit if/else writing both polarities; keeps the markedSkipped
        # sub-call. Branch shape differs from the frozen closed-form; still correct.
        "module": _td(
            "    let skipped ← markedSkipped skipMarked\n"
            "    if !asyncTest && debuggerActive && !skipped then\n"
            "      return true\n"
            "    else\n"
            "      return false"),
        "rationale": "second structurally-different CORRECT impl: an explicit "
        "if/else writing both polarities (frozen returns a closed-form bool), "
        "still routing the skip read through the markedSkipped sub-call. Must "
        "verify against (T), else the clause is over-fit to the closed-form SHAPE "
        "=> SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-ms-doubleneg",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different CORRECT impl of the sub-method: double negation.
        "module": _ms("    return (!(!skipMarked))"),
        "rationale": "structurally-different CORRECT impl of the markedSkipped "
        "sub-method (double negation `!(!skipMarked)`, observationally the "
        "identity). Must verify against clause (M) `out = skipMarked`, else that "
        "obligation is SPEC-TOO-STRONG. Defends the sub-method's own contract, "
        "which the caller's proof consumes.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling constructs an F2P-shaped input and asserts the
    # Requires facts are establishable. There is NO `require` clause here, so that
    # probe is vacuous. Re-aimed at the residual total-domain risk: the decision
    # the impl actually computes is non-degenerate over the METHOD'S OWN BINDERS.
    #
    # AUDIT REPAIR. The ported form asserted `(!false && true && !true) = false`
    # and `(!false && true && !false) = true` — closed Bool LITERALS. Those are
    # theorems of boolean algebra: they mention no binder, no impl term and no
    # `ensures` clause, so they discharge identically inside any impl (and inside
    # the frozen file), and the case attested only that `loom_solve` still closed
    # the untouched obligation. Re-aimed at three claims over the real binders:
    #   (1) `skipped = skipMarked` — the sub-method contract (M) is genuinely
    #       consumed at the call site, not merely present;
    #   (2) `decision = (!asyncTest && debuggerActive && !skipMarked)` — the value
    #       the impl computes THROUGH the sub-call coincides with clause (T)'s
    #       right-hand side over the caller's own inputs;
    #   (3) `(debuggerActive && !asyncTest) → decision = !skipMarked` — on the
    #       debugger-active non-async sub-domain the decision is a NON-CONSTANT
    #       function of the skip mark, i.e. the post-image discriminates a
    #       skip-marked test from a non-skipped one there. This is the
    #       non-degeneracy the literal pair only gestured at.
    # Each was checked to be load-bearing by a negative control: flipping any one
    # of the three leaves an unsolved goal and the build fails. The impl's own
    # dataflow is kept verbatim so the method's `ensures` still discharges under
    # the frozen loom_solve.
    # =====================================================================
    {
        "id": "admiss-f2p-shape-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _td(
            "    let skipped ← markedSkipped skipMarked\n"
            "    assert (with_name_prefix `admiss (skipped = skipMarked))\n"
            "    let decision := !asyncTest && debuggerActive && !skipped\n"
            "    assert (with_name_prefix `admiss2 (decision = (!asyncTest && debuggerActive && !skipMarked)))\n"
            "    assert (with_name_prefix `admiss3 ((debuggerActive && !asyncTest) → decision = !skipMarked))\n"
            "    return decision"),
        "rationale": "the decision the impl computes is non-degenerate over the "
        "METHOD'S OWN BINDERS, not merely at hardcoded literals. Three in-region "
        "asserts, each independently load-bearing (flipping any one leaves an "
        "unsolved goal and the build fails): `skipped = skipMarked` shows the "
        "sub-method contract (M) is actually consumed at the call site; "
        "`decision = (!asyncTest && debuggerActive && !skipMarked)` shows the "
        "value computed THROUGH the sub-call coincides with clause (T)'s "
        "right-hand side over the caller's inputs; and "
        "`(debuggerActive && !asyncTest) → decision = !skipMarked` shows that on "
        "the debugger-active non-async sub-domain the decision is a NON-CONSTANT "
        "function of the skip mark — it distinguishes a skip-marked test under "
        "the debugger (not deferred) from a non-skipped one (deferred), exactly "
        "the behaviour the fix demands. The impl's dataflow is kept verbatim so "
        "the method's own `ensures` still discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each is a closed-form decision with a machine-checked
    # refutation witness at a concrete boolean point, and a refinement argument
    # for why its faithful real counterpart would NOT resolve the failing test.
    # Witness points (asyncTest, debuggerActive, skipMarked) are chosen to VARY
    # every binder across the reject set.
    # =====================================================================

    # ---- clause (T), skipMarked binder: the PRE-PATCH shape ----
    {
        "id": "td-prepatch-ignore-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # Defer whenever non-async and debugger active, IGNORING the skip mark —
        # the exact pre-patch behaviour. Correct on every not-skipped point;
        # diverges on non-async + debugger + skip-marked (defers where the spec
        # forbids it). This is precisely the F2P scenario.
        "module": _td_rival("!asyncTest && debuggerActive"),
        "refinement": "this is the literal PRE-PATCH decision (no skip exclusion). "
        "The failing test runs a skip-marked test under the interactive "
        "post-mortem debugger and asserts its teardown is NOT run; the pre-patch "
        "defers teardown, which is then invoked later, so the test FAILS. It is the "
        "bug under repair (confirmed by Solution_prepatch.lean / G-DIFF) and does "
        "NOT resolve.",
        "rationale": "REJECT from the biconditional (T): diverges on "
        "asyncTest=false ^ debuggerActive=true ^ skipMarked=true (returns true; "
        "spec requires false). Verifying would be SPEC-TOO-WEAK on the skip "
        "exclusion. Refuted at exactly that point — the sub-domain the F2P "
        "exercises.",
        "witness": _td_tester(
            "example : teardownPostponedTester false true true = false := by\n"
            "  decide\n"),
    },

    # ---- clause (T), skipMarked binder: INVERTED skip guard ----
    {
        "id": "td-invert-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # Defer only when non-async AND debugger AND SKIPPED — records exactly the
        # cases that must not defer, and skips the ones that must. Diverges on both
        # the skipped point (defers, must not) and the not-skipped point (does not
        # defer, must).
        "module": _td_rival("!asyncTest && debuggerActive && skipMarked"),
        "refinement": "a real patch guarding on the skip mark with the wrong "
        "polarity (deferring only for a skip-marked test) would still defer the "
        "skipped test's teardown (F2P still fails) AND stop deferring for the "
        "ordinary debugger case, so the non-skipped debugger companion would no "
        "longer postpone teardown correctly -> it would NOT resolve.",
        "rationale": "REJECT from (T) on BOTH the skipped and not-skipped "
        "sub-domains (the skip conjunct is inverted). Refuted at the not-skipped "
        "debugger point (non-async, debugger, NOT skipped): gold defers (true), the "
        "rival does not (false).",
        "witness": _td_tester(
            "example : teardownPostponedTester false true false = false := by\n"
            "  decide\n"),
    },

    # ---- clause (T), debuggerActive binder: IGNORE the debugger flag ----
    {
        "id": "td-ignore-debugger",
        "kind": "uniqueness",
        "expect": "reject",
        # Defer whenever non-async and not-skipped, regardless of the debugger.
        # Correct on the whole debugger-active sub-domain; diverges when the
        # debugger is inactive (defers where spec requires no deferral).
        "module": _td_rival("!asyncTest && !skipMarked"),
        "refinement": "a real patch dropping the debugger half of the guard would "
        "defer teardown for EVERY ordinary non-skipped test, even without the "
        "debugger -- changing the moment the test instance interacts with the "
        "results object for the whole ordinary unittest suite (the source itself "
        "warns this is done only when absolutely needed). The non-debugger P2P "
        "unittest/teardown grid would observe postponed teardown and fail -> it "
        "would NOT resolve.",
        "rationale": "REJECT from (T) on the debugger-inactive sub-domain "
        "(debuggerActive=false -> postpone must be false, but this defers for any "
        "non-async not-skipped test). Refuted at the debugger-OFF point (non-async, "
        "no debugger, not skipped): gold does not defer (false), the rival does "
        "(true).",
        "witness": _td_tester(
            "example : teardownPostponedTester false false false = false := by\n"
            "  decide\n"),
    },

    # ---- clause (T), asyncTest binder: IGNORE the async flag ----
    {
        "id": "td-ignore-async",
        "kind": "uniqueness",
        "expect": "reject",
        # Defer whenever debugger active and not-skipped, regardless of async.
        # Correct on the whole non-async sub-domain; diverges for an async test
        # (defers where the deferral must never apply). This binder has NO nagini
        # counterpart (the sibling models only mode × marker); it is the one the
        # narrowed spec adds, so the reject set must move it.
        "module": _td_rival("debuggerActive && !skipMarked"),
        "refinement": "a faithful patch applying the deferral without the "
        "non-async guard would postpone teardown on the asynchronous path too, "
        "where the test is driven entirely by its own framework and this mechanism "
        "must never intervene -- so an async test's teardown timing would change "
        "and the async unittest P2P behaviour would observe it -> it would NOT "
        "resolve.",
        "rationale": "REJECT from (T) on the async sub-domain (asyncTest=true -> "
        "postpone must be false, but this defers for any debugger not-skipped "
        "test). Refuted at the async point (ASYNC, debugger, not skipped): gold "
        "does not defer (false), the rival does (true). This is the binder no "
        "other witness abuses.",
        "witness": _td_tester(
            "example : teardownPostponedTester true true false = false := by\n"
            "  decide\n"),
    },

    # ---- clause (T), coarse near-miss: defer UNCONDITIONALLY ----
    {
        "id": "td-always",
        "kind": "uniqueness",
        "expect": "reject",
        # Defer for every input. Correct only where the gold decision is true;
        # diverges on every point where it is false. A coarse supporting near-miss
        # any tight biconditional rejects.
        "module": _td_rival("true"),
        "refinement": "a real patch that always deferred teardown would postpone "
        "it for every test (async or not, skipped or not, debugger or not) -> the "
        "F2P (skipped -> deferred -> teardown runs) and the ordinary non-debugger "
        "P2P suite both fail -> it would NOT resolve.",
        "rationale": "REJECT from (T) whenever the gold decision is false. Carried "
        "as a coarse supporting near-miss alongside the reasoned attacks. Refuted "
        "at an async + no-debugger + skipped point (three binders all at the "
        "value that forces gold false): gold false, rival true.",
        "witness": _td_tester(
            "example : teardownPostponedTester true false true = false := by\n"
            "  decide\n"),
    },

    # ---- clause (T), MINIMAL near-miss: agree with gold except at ONE point ----
    # AUDIT ADDITION. Every ported td-* rival drops or flips a whole conjunct, so
    # each is wrong on a HALF-CUBE. None tests the tightest thing a biconditional
    # claims: that a single erroneous point is enough to reject. This rival is the
    # gold decision OR-ed with the one extra cube point (async ^ debugger ^
    # skipped) — correct on 7 of 8 inputs, wrong on exactly one. It also moves the
    # skipMarked binder at the async+debugger corner no other witness probes.
    {
        "id": "td-single-point-defer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _td_rival(
            "(!asyncTest && debuggerActive && !skipMarked) "
            "|| (asyncTest && debuggerActive && skipMarked)"),
        "refinement": "a faithful counterpart would carry the correct guard but "
        "add one further branch that ALSO defers a skip-marked asynchronous test "
        "under the debugger. That is doubly wrong on the real path: the deferral "
        "must never apply on the asynchronous path (driven by its own framework), "
        "and it must never apply to a skip-marked test. The async and skipped P2P "
        "teardown rows would observe teardown deferred where the mechanism must "
        "not intervene -> it would NOT resolve.",
        "rationale": "REJECT from (T) at a SINGLE point of the cube: the rival "
        "agrees with the biconditional on 7 of 8 inputs and diverges only at "
        "asyncTest=true ^ debuggerActive=true ^ skipMarked=true (returns true; "
        "spec requires false). Establishes that the clause is tight point-wise, "
        "not merely half-cube-wise — the strongest form of SPEC-TOO-WEAK probe "
        "for a complete biconditional, and the one the conjunct-dropping rivals "
        "cannot make.",
        "witness": _td_tester(
            "example : teardownPostponedTester true true true = false := by\n"
            "  decide\n"),
    },

    # ---- clause (T), skipMarked binder: skip mark as an alternative TRIGGER ----
    # AUDIT ADDITION. Refuted at (false, false, true) — the debugger-OFF,
    # skip-marked point, which NO ported witness probes (td-ignore-debugger sits
    # at debugger-off but NOT skipped; td-always sits at skipped but async).
    {
        "id": "td-skip-as-trigger",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _td_rival("!asyncTest && (debuggerActive || skipMarked)"),
        "refinement": "a faithful counterpart that treated the skip mark as a "
        "REASON to defer (rather than a reason not to) would defer teardown for "
        "every skip-marked non-async test even with no debugger in use — so an "
        "ordinarily-skipped test's teardown would be postponed and then run, in a "
        "run where the deferral mechanism should never engage at all. Both the "
        "skip-marked failing scenario and the ordinary skip P2P rows would "
        "observe it -> it would NOT resolve.",
        "rationale": "REJECT from (T) on the debugger-INACTIVE skip-marked "
        "sub-domain: the skip conjunct is not merely inverted but promoted from an "
        "exclusion to an independent trigger, so the rival defers where BOTH "
        "reasons to defer are absent. Refuted at (non-async, NO debugger, "
        "skip-marked): gold does not defer (false), the rival does (true). That "
        "point is probed by no other witness in this battery.",
        "witness": _td_tester(
            "example : teardownPostponedTester false false true = false := by\n"
            "  decide\n"),
    },

    # ---- clause (M) consumed at the CALL SITE: miswired sub-call argument ----
    # AUDIT ADDITION. Every other rival edits a boolean SHAPE; this one keeps the
    # frozen decision expression byte-for-byte and corrupts only the DATAFLOW into
    # the sub-method, feeding it the wrong binder. It is the one rival that
    # attacks the caller/callee wiring rather than the caller's own algebra.
    {
        "id": "td-miswire-subcall-arg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _td(
            "    let skipped ← markedSkipped asyncTest\n"
            "    let decision := !asyncTest && debuggerActive && !skipped\n"
            "    return decision"),
        "refinement": "a faithful counterpart would route the skip-mark query at "
        "the wrong object — asking whether the test is asynchronous instead of "
        "whether it bears a skip mark — while leaving the deferral expression "
        "exactly right. The skip exclusion would then never fire for a skip-marked "
        "test, so a skip-marked test under the debugger still has its teardown "
        "deferred and run: the failing scenario is unchanged -> it would NOT "
        "resolve.",
        "rationale": "REJECT from (T) via the sub-method's DATAFLOW, not the "
        "caller's algebra: the frozen decision expression is kept verbatim and "
        "only the argument passed to markedSkipped is miswired, so clause (M) is "
        "discharged about the wrong value and the composed result no longer meets "
        "(T). Refuted at (non-async, debugger, skip-marked) — the rival reads "
        "`asyncTest=false` as 'not skipped' and defers (true) where the spec "
        "requires false. No other rival in this battery attacks the call-site "
        "wiring; all the rest reshape the boolean expression.",
        "witness": _td_tester(
            "example : teardownPostponedTester false true true = false := by\n"
            "  decide\n"),
    },

    # ---- clause (M): the sub-method's own identity contract ----
    {
        "id": "ms-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant true: reports every object as skip-marked. Correct only on the
        # skip-marked sub-domain; diverges on any non-marked object. Attacks the
        # sub-method obligation (M) directly.
        "module": _ms("    return true"),
        "refinement": "a skip-mark query that always reported 'marked' would treat "
        "every test as skipped: collection would inject no setup/teardown fixtures "
        "and the xunit fixture would skip every test, so ordinary tests would stop "
        "running -> the whole non-skipped P2P suite fails -> it would NOT resolve.",
        "rationale": "REJECT from clause (M) `out = skipMarked`: a constant `true` "
        "disagrees on every non-marked object. Attacks the markedSkipped "
        "obligation the caller's proof consumes. Refuted at the not-marked input "
        "(skipMarked=false): gold reports false, the rival true.",
        "witness": _ms_tester(
            "example : markedSkippedTester false = false := by\n"
            "  decide\n"),
    },
    {
        "id": "ms-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant false: reports every object as NOT skip-marked. Correct only on
        # the not-marked sub-domain; diverges on any marked object. The
        # complement of ms-const-true, so the markedSkipped binder is varied.
        "module": _ms("    return false"),
        "refinement": "a skip-mark query that always reported 'not marked' would "
        "run and defer teardown for a genuinely skip-marked test under the "
        "debugger (the F2P scenario), since the deferral decision would see no "
        "mark to exclude -> the F2P test fails and it would NOT resolve.",
        "rationale": "REJECT from clause (M) `out = skipMarked`: a constant `false` "
        "disagrees on every marked object. Complements ms-const-true so the "
        "markedSkipped binder is moved across the reject set. Refuted at the marked "
        "input (skipMarked=true): gold reports true, the rival false.",
        "witness": _ms_tester(
            "example : markedSkippedTester true = false := by\n"
            "  decide\n"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
# The sibling battery has 9 SPEC cases (2 soundness positives, 1 admissibility,
# 6 uniqueness rivals) plus an EMPTY AXIOM lane. It models one contracted
# operation `decide_teardown(item)` over a permission-bearing struct with two
# read-only fields (postmortem_mode, skip_marker) and one mutated field
# (teardown_recorded), specified by a biconditional over mode × marker.
#
# This bundle models the SAME purely-functional core as TWO boolean methods:
# `teardownPostponed` (the deferral decision, biconditional (T) over THREE
# inputs) and its sub-method `markedSkipped` (the skip-mark read, identity (M)).
# The velvet spec adds a THIRD binder the sibling never modeled — asyncTest — and
# surfaces the skip read as its own contracted callee. The value surface carries
# across; the permission surface does not exist here.
#
#   sibling case              -> here                              disposition
#   --------------------------------------------------------------------------
#   pos-uncond                -> pos-td-direct                     PORTED
#   pos-ifelse                -> pos-td-ifelse                     PORTED
#   (no sibling)              -> pos-ms-doubleneg                  ADDED (sub-method defence)
#   admiss-pdb-skipped        -> admiss-f2p-shape-nondegenerate    RE-AIMED
#   frame-write-mode          -> (none)                            VACUOUS
#   frame-write-marker        -> (none)                            VACUOUS
#   pd-prepatch               -> td-prepatch-ignore-skip           PORTED
#   pd-invert                 -> td-invert-skip                    PORTED
#   pd-ignore-pdb             -> td-ignore-debugger                PORTED
#   pd-always                 -> td-always                         PORTED
#   (no sibling)              -> td-ignore-async                   ADDED (asyncTest binder)
#   (no sibling)              -> ms-const-true                     ADDED (clause M attack)
#   (no sibling)              -> ms-const-false                    ADDED (clause M, varies binder)
#   (no sibling)              -> td-single-point-defer              ADDED BY AUDIT (point-wise tightness)
#   (no sibling)              -> td-skip-as-trigger                 ADDED BY AUDIT (unprobed cube point)
#   (no sibling)              -> td-miswire-subcall-arg             ADDED BY AUDIT (call-site dataflow)
#   AXIOM_TESTS ([])          -> (none)                            DROPPED (G-AX skip)
#
# 6 ported, 1 re-aimed (then REPAIRED by audit), 7 added (4 at port time, 3 by
# the audit), 2 vacuous, 0 dropped-for-difficulty.
#
# AUDIT REPAIRS (independent adversarial re-derivation of this port):
#  * admiss-f2p-shape-nondegenerate had asserted two closed Bool LITERAL
#    identities. Those are theorems of boolean algebra mentioning no binder, no
#    impl term and no `ensures` clause — they discharge inside any impl, so the
#    case attested only that the untouched obligation still closed. Re-aimed at
#    three claims over the method's own binders (sub-contract consumed at the
#    call site; computed decision equals clause (T)'s RHS; the decision is a
#    NON-CONSTANT function of the skip mark on the debugger-active non-async
#    sub-domain). Each verified load-bearing by a negative control: flipping any
#    one leaves an unsolved goal and the build fails.
#  * Three rivals added. Every ported td-* rival drops or flips a whole conjunct,
#    so each is wrong on a half-cube; and two cube points went unprobed.
#    td-single-point-defer is wrong at exactly ONE of the 8 points (point-wise
#    tightness, the strongest SPEC-TOO-WEAK probe a complete biconditional
#    admits); td-skip-as-trigger is refuted at (non-async, no debugger,
#    skip-marked), a point no ported witness touches; td-miswire-subcall-arg
#    keeps the frozen decision expression verbatim and corrupts only the ARGUMENT
#    passed to the sub-method, the one rival attacking caller/callee wiring
#    rather than boolean algebra.
#  * SPEC PROBES, no hole found. 6 new wrong impls (constant false, disjunction
#    for conjunction, negated sub-method, and the three shipped above) were all
#    rejected on the `ensures_1` goal. 6 new CORRECT reshapes (De Morgan, conjunct
#    reordering, nested if with early false, double negation, sub-method if/else,
#    and a redundantly-conjoined form) all VERIFIED — so the spec is neither too
#    weak nor too strong on any probe run. Gold's extracted tester was checked to
#    be `true` at all 8 cube points, which is what makes every `Tester ... = false`
#    witness a non-tautology.
# Divergence lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
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
# 14 SPEC cases total:
#   3 soundness    : pos-td-direct, pos-td-ifelse, pos-ms-doubleneg
#   1 admissibility: admiss-f2p-shape-nondegenerate
#  10 uniqueness   : td-prepatch-ignore-skip, td-invert-skip, td-ignore-debugger,
#                    td-ignore-async, td-always, td-single-point-defer,
#                    td-skip-as-trigger, td-miswire-subcall-arg, ms-const-true,
#                    ms-const-false
#
# PORTED (2 positives). pos-uncond computed the decision into a local and wrote
#   it unconditionally; pos-td-direct is the velvet analogue (return the grounded
#   expression directly, no branch). pos-ifelse becomes pos-td-ifelse (explicit
#   if/else writing both polarities). Both keep the frozen loom_solve proof and
#   were confirmed to build.
# ADDED (pos-ms-doubleneg). The sibling contracts a single function; velvet
#   surfaces the skip read as its OWN sub-method with obligation (M), so it needs
#   its own positive control (a double-negation reshape) and its own attacker
#   (ms-const-true) — coverage of a surface the sibling did not model separately.
# RE-AIMED, then REPAIRED BY AUDIT (admissibility). The sibling asserts the
#   Requires facts are establishable on an F2P-shaped item; there is NO `require`
#   clause here, so that probe is vacuous. The port re-aimed it at non-degeneracy
#   but stated it with closed Bool LITERALS, which discharge by boolean algebra
#   independently of the impl and of the spec — passing honestly while testing
#   nothing. Now stated over the METHOD'S OWN BINDERS: the sub-contract is
#   consumed at the call site (`skipped = skipMarked`), the computed decision
#   coincides with clause (T)'s RHS, and on the debugger-active non-async
#   sub-domain the decision is a NON-CONSTANT function of the skip mark. Each
#   assert independently confirmed load-bearing by a negative control. Impl
#   dataflow kept verbatim; confirmed to build.
# PORTED (4 rivals). pd-prepatch -> td-prepatch-ignore-skip (drop the skip
#   exclusion — the exact bug). pd-invert -> td-invert-skip (skip conjunct
#   polarity flipped). pd-ignore-pdb -> td-ignore-debugger (drop the debugger
#   half). pd-always -> td-always (defer unconditionally). Each refinement
#   argument carries over: a faithful counterpart with that defect still
#   mis-defers on the failing scenario or breaks a P2P suite, so it would NOT
#   resolve.
# ADDED (td-ignore-async). velvet's spec models a third binder, asyncTest, that
#   the sibling's mode × marker carrier lacks. Per the coverage contract every
#   binder must be varied by the reject set, so this rival (defer regardless of
#   async) moves the binder no other witness touches.
# VACUOUS (frame-write-mode, frame-write-marker). The sibling carries these
#   MANDATORY because postmortem_mode / skip_marker are held at half permission
#   and a store into either is rejected for insufficient permission. This backend
#   is referentially transparent, declares no `mut` binder over any input (every
#   input is an immutable Bool), and has no heap — so there is no read-only input
#   to overwrite and no permission system to trip. Not fabricated (porting map:
#   vacuous here).
# DROPPED (AXIOM_TESTS). The sibling's axiom lane is empty (skip_marker_set is a
#   fully-unfolded deep model, not a consumed axiom). This bundle declares no
#   axioms and no deep-model references (mapping.md §3; G-AX skip), so there is
#   nothing to probe — and this gate ignores AXIOM_TESTS regardless.
#
# No case was dropped because its proof would not close. All three soundness
# positives and the admissibility probe verify under the frozen `loom_solve`.
#
# BINDER / CLAUSE COVERAGE. Two obligations, both defended and attacked:
#   * (M) `out = skipMarked` — defended by pos-ms-doubleneg, attacked by
#     ms-const-true (at skipMarked=false) and ms-const-false (at skipMarked=true),
#     so the sub-method's single binder is moved across the reject set.
#   * (T) `postpone = (!asyncTest && debuggerActive && !skipMarked)` — defended
#     by pos-td-direct / pos-td-ifelse / admiss, attacked by the eight td-* rivals
#     across distinct sub-domains (drop skip / invert skip / drop debugger / drop
#     async / defer always / one-point over-defer / skip promoted to a trigger /
#     miswired sub-call argument).
#   All three (T) binders are VARIED across the reject witnesses. Points
#   (asyncTest, debuggerActive, skipMarked):
#     td-prepatch-ignore-skip : (false, true,  true)
#     td-invert-skip          : (false, true,  false)
#     td-ignore-debugger      : (false, false, false)
#     td-ignore-async         : (true,  true,  false)
#     td-always               : (true,  false, true)
#     td-single-point-defer   : (true,  true,  true)
#     td-skip-as-trigger      : (false, false, true)
#     td-miswire-subcall-arg  : (false, true,  true)
#   asyncTest      moves false/false/false/true/true/true/false/false;
#   debuggerActive moves true/true/false/true/false/true/false/true;
#   skipMarked     moves true/false/false/false/true/true/true/true.
#   So no binder is held constant, and SEVEN of the eight cube points are probed
#   (only (true,false,false) is not — the point at which every conjunct-level
#   defect and gold agree on `false`). td-miswire-subcall-arg shares its tuple
#   with td-prepatch-ignore-skip deliberately: same discriminating point, a
#   different DEFECT CLASS (call-site dataflow vs. caller algebra). ms-const-true /
#   ms-const-false probe markedSkipped at skipMarked=false and skipMarked=true.
# WITNESS DISCRIMINATION. Independently re-derived by the audit with two real
#   builds per reject case (10 cases, 20 builds): each witness ELABORATES against
#   its rival (exit 0 — the extracted tester `decide`s to false, so the rival's
#   output violates the postcondition at the probed point) and FAILS against the
#   frozen solution (exit 1). Every gold-side failure was read and is a SEMANTIC
#   refutation — `Tactic 'decide' proved that the proposition <tester> = false is
#   false`, i.e. the kernel evaluated the claim and found gold's tester `true`
#   there. None is a stuck reduction, an unknown identifier, a type error or a
#   timeout. Gold's tester was additionally confirmed `true` at ALL 8 cube points
#   (and both markedSkipped points), which is what rules out a tautological
#   witness. No witness binds a hypothesis (fully transparent Bool carrier), so no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears in any witness.
AXIOM_TESTS = []
