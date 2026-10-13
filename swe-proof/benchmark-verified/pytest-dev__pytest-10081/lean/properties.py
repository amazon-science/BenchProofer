"""properties.py — G-PBT falsification battery for pytest-dev__pytest-10081 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each ``SPEC_TESTS`` case is a
full ``Solution.lean`` variant produced by REGION SURGERY: only text inside the
``-- impl-start`` / ``-- impl-end`` region — and, for the case that legitimately
re-proves, inside the ``-- proof-start`` / ``-- proof-end`` region — is changed.
So ``markers.same_spec`` holds by construction, the single
``theorem correct_deferTeardown`` STATEMENT stays byte-identical, and no case
introduces an ``axiom`` / ``sorry`` / ``admit`` / ``native_decide`` or a new
top-level ``theorem``/``lemma``. ``expect="verify"`` passes iff the variant is in
scope AND the obligation actually closes for the RESHAPED implementation;
``expect="reject"`` passes iff the variant is in scope AND it does not verify AND
the case's refutation ``witness`` holds of the rival while FAILING on the frozen
solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini sibling
contracts the decision over a heap object (a record whose two skip facets are held
at fractional read permission) and pins six separate postcondition clauses — a
main equality plus four one-directional implications and a frame clause. This
Lean bundle models the SAME single purely-functional core, over three plain
``Bool`` inputs, and collapses those clauses into ONE biconditional equality (see
DEFENDED SURFACE). Every nagini case whose argument survives that narrowing is
carried over as an attack on that equality or as a faithful correct positive; the
nagini frame/permission-mutation class is VACUOUS here (see ``assessment``).

DEFENDED SURFACE (one modeled behavior; one top-level clause).
``problem_spec_deferTeardown pdbEnabled testItselfSkipped classSkipped result``
pins EXACTLY::

    result = (pdbEnabled && !(testItselfSkipped || classSkipped))

The single output component is therefore left NO freedom: the equality is a
biconditional, so it subsumes each of the nagini sibling's one-directional
clauses at once. Written out, it simultaneously demands

  * (necessity of the enabled option) the step is never specially deferred while
    the interactive debugger is not enabled;
  * (each marker decisive, independently) the step is never specially deferred
    when the test itself is marked skip, and never when its containing class is
    marked skip — the two observations are combined DISJUNCTIVELY, so either one
    alone suppresses the deferral;
  * (the positive direction) when the debugger IS enabled and NEITHER marker is
    set, the step MUST be specially deferred — this is what stops the disjunction
    from being read as a conjunction, and what keeps the ordinary
    nothing-is-skipped run behaving as before.

The BEHAVIOURAL DISCRIMINATOR (the fix): the "is this test going to run at all"
observation must consult the containing class's marker as well as the test's own.
The earlier behavior consulted only the test's own marker, so a test whose
CONTAINING CLASS carries the marker was treated as live and its teardown step was
specially intercepted and later replayed — running teardown for a test that never
ran. The ``weak-drop-class-skip`` rival below IS that earlier behavior.

BINDER STRUCTURE. The spec predicate has THREE input binders: ``pdbEnabled``,
``testItselfSkipped``, ``classSkipped``. All three are load-bearing and all three
are VARIED across the reject witnesses — see the point-spread block at the bottom
of this file: the seven reject cases probe ALL EIGHT input triples, and each
binder takes both ``true`` and ``false`` somewhere in that set. In particular
``pdbEnabled`` is moved to ``false`` by ``weak-ignore-pdb-option`` (a rival that
would otherwise verify unnoticed if every witness held the option enabled), and
the all-markers-set triple and the nothing-skipped triple are each probed by their
own rival, so no sub-domain of the eight-point input space is defended only by the
positives.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's two mandatory
    frame probes overwrite a read-only input facet of the heap record and are
    rejected for insufficient permission rather than for a wrong value. Lean is
    referentially transparent: the three inputs are immutable ``Bool`` values,
    there is no heap, no aliasing, no fractional permission, and no ``mut`` input
    binder to overwrite. There is nothing to mutate and so nothing to reject, and
    no substitute probe is fabricated (porting map: vacuous here).

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend, and vacuous for a
    structural reason rather than because the spec admits it: the modeled
    behavior is a total Lean ``def`` over ``Bool`` inputs, so a diverging
    implementation cannot be written at all. (This is the lean disposition
    recorded in ``the corpus-wide termination-semantics finding``; the KNOWN-HOLE disposition
    described there applies to the partial-semantics backend, not here.) The
    nagini sibling carries no divergence case either.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: the result
    is pinned to a boolean expression over the three input observations
    themselves, with no opaque callee and no answer key to echo. Recomputing that
    expression IS doing the work. In its place the battery carries honest
    cheapest-implementation POSITIVE CONTROLS that must verify (the nagini
    sibling makes the same call for the same reason).

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject lane. Seven rivals,
    each correct on part of the eight-point domain and wrong where one aspect of
    the clause bites: consult only the test's own marker (the earlier behavior);
    consult only the containing class's marker; combine the two markers
    conjunctively instead of disjunctively; ignore the markers entirely; ignore
    the debugger-enabled option entirely; invert the decision; and relate the
    option to the markers by inequality rather than by
    conjunction-with-negation (added by audit, to probe the three
    option-disabled marked triples the other six leave alone).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states ``¬ problem_spec_deferTeardown`` at
one concrete boolean triple, applied to the RIVAL's own
``implementation_deferTeardown`` at that triple, and closes by ``decide`` after
unfolding both. Every input is a ground ``Bool`` literal, so each witness head
binds NOTHING: there are no hypotheses whose joint satisfiability could be in
question, and no conditioning on an opaque carrier is needed (this bundle
declares no ``opaque`` callee). Each witness was checked with two real
``lake env lean`` builds — it HOLDS of its rival and FAILS on the frozen solution
— so it discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful counterpart in the real
codebase decides the interception differently on an input the project's own
regression tests exercise, so the added regression coverage (a test whose
containing class carries the skip marker, run with the interactive debugger
enabled, asserting that neither the per-test setup nor the per-test teardown is
invoked) or the pre-existing coverage (teardown IS eventually invoked for a live
test under the debugger; teardown is NOT invoked for a test whose own marker is
set) would fail. Any such rival that nonetheless verified would therefore be a
genuine verify-does-not-imply-resolve break, not an artifact.

AXIOM lane: EMPTY here. This bundle declares no ``opaque`` callee and consumes no
``axiom`` — every observation enters as plain boolean data — so there is no
callee contract to probe. The nagini sibling's single ``AXIOM_TESTS`` entry
(grounding its pure identity helper against the real predicate) is DROPPED: the
axiom lane belongs to G-AX, and this gate ignores it.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-10081"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it edits and is unique in
# Solution.lean (checked at load by _swap), so the manifest breaks loudly if the
# frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The whole body of `implementation_deferTeardown`, inside `-- impl-start` /
# `-- impl-end`: the combined observation, the guard, and the two exits. Every
# reject rival and every positive control replaces exactly this text, so no case
# can touch the spec view.
_I_BODY = (
    "  let skipped := testItselfSkipped || classSkipped\n"
    "  if pdbEnabled && !skipped then\n"
    "    return true\n"
    "  return false"
)

# The frozen proof's `intro` line, inside `-- proof-start` / `-- proof-end`, so
# the admissibility case can prepend ground `have`s without touching the
# `correct_deferTeardown` STATEMENT or the spec view.
_P_INTRO = "  intro pdbEnabled testItselfSkipped classSkipped\n"


def _impl(body: str) -> str:
    """A full Solution.lean whose implementation body is `body`."""
    return _swap(_BASE, _I_BODY, body.rstrip("\n"))


# ---------------------------------------------------------------------------
# Witness scaffold. States that the spec FAILS of the rival's own output at one
# concrete input triple. Ground literals only, so the head binds nothing and the
# gate's consistency probe is not even needed.
# ---------------------------------------------------------------------------
def _w(pdb: str, obj: str, cls: str) -> str:
    return (
        f"example : ¬ problem_spec_deferTeardown {pdb} {obj} {cls}\n"
        f"    (implementation_deferTeardown {pdb} {obj} {cls}) := by\n"
        "  unfold problem_spec_deferTeardown implementation_deferTeardown\n"
        "  decide\n"
    )


SPEC_TESTS = [

    # =====================================================================
    # SOUNDNESS (positive controls) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `correct_deferTeardown` statement byte-identical; the frozen proof body
    # (an exhaustive `cases` split closed by `rfl`) is left untouched and still
    # closes, because a total case split over three `Bool`s is insensitive to the
    # body's shape. No proof authoring, no helper lemma, no assumption token.
    # (All three confirmed by a real build.)
    # =====================================================================

    # Ports nagini POSITIVE CONTROL A (branch-reorder / nested-if reshape).
    {
        "id": "pos-control-cascade",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "  if !pdbEnabled then\n"
            "    return false\n"
            "  if testItselfSkipped then\n"
            "    return false\n"
            "  if classSkipped then\n"
            "    return false\n"
            "  return true"
        ),
        "rationale": "a CORRECT implementation with a different control-flow shape "
                     "must verify. Instead of one combined guard it uses a cascade "
                     "of early-return refusals — not enabled, then each marker in "
                     "turn — reaching the deferral only when all three refusals are "
                     "passed. That returns true exactly when the option is enabled "
                     "and neither marker is set, i.e. the spec's equality holds at "
                     "every one of the eight input triples. The named intermediate "
                     "observation is gone entirely, so nothing about the frozen "
                     "body's shape is relied upon. If this fails to verify the spec "
                     "is SPEC-TOO-STRONG (it would be pinning a control-flow shape "
                     "rather than the decision). Ports the nagini nested-if "
                     "positive control.",
    },

    # Ports nagini POSITIVE CONTROL B (De Morgan reshape, single expression).
    {
        "id": "pos-control-demorgan",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "  return pdbEnabled && !testItselfSkipped && !classSkipped"
        ),
        "rationale": "the cheapest correct implementation, written as a conjunction "
                     "of negations rather than as a negated disjunction. De Morgan "
                     "makes it the same boolean function of the three inputs, so the "
                     "spec's equality still holds everywhere and it must verify. It "
                     "also removes the guard and both exits, collapsing the body to "
                     "a single expression — the maximal reshape short of changing "
                     "the decision — so it is the strongest available check that the "
                     "spec constrains the VALUE and not the phrasing. Stands in for "
                     "an ungrounded-oracle echo, of which none exists on this "
                     "carrier (the postcondition is grounded in the inputs "
                     "themselves). Else SPEC-TOO-STRONG. Ports the nagini De Morgan "
                     "positive control.",
    },

    # Extra positive with no nagini counterpart: exhaustive tabulation.
    {
        "id": "pos-control-tabulated",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "  match pdbEnabled, testItselfSkipped, classSkipped with\n"
            "  | true, false, false => return true\n"
            "  | _, _, _ => return false"
        ),
        "rationale": "a CORRECT implementation that uses no boolean algebra at all: "
                     "it tabulates the decision by matching the three observations "
                     "simultaneously and defers only for the single triple where "
                     "the option is enabled and neither marker is set. This is the "
                     "extensional statement of the same function, so it must "
                     "verify. Its value as a positive is that it shares NO syntactic "
                     "structure with the frozen body — no disjunction, no negation, "
                     "no guard — so a spec that had accidentally been pinned to the "
                     "frozen phrasing (or a proof that only closed for it) would be "
                     "caught here. Else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY
    # =====================================================================
    {
        "id": "admiss-ground-points",
        "kind": "admissibility",
        "expect": "verify",
        # Ground `have`s prepended INSIDE the proof region, before the frozen
        # `intro`; the frozen tactic script follows unchanged and the theorem
        # STATEMENT is byte-identical. Adds no top-level declaration.
        "module": _swap(
            _BASE, _P_INTRO,
            "  have h_class_only : problem_spec_deferTeardown true false true\n"
            "      (implementation_deferTeardown true false true) := by\n"
            "    unfold problem_spec_deferTeardown implementation_deferTeardown\n"
            "    decide\n"
            "  have h_live : problem_spec_deferTeardown true false false\n"
            "      (implementation_deferTeardown true false false) := by\n"
            "    unfold problem_spec_deferTeardown implementation_deferTeardown\n"
            "    decide\n"
            "  have h_option_off : problem_spec_deferTeardown false false false\n"
            "      (implementation_deferTeardown false false false) := by\n"
            "    unfold problem_spec_deferTeardown implementation_deferTeardown\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the admissibility question the nagini sibling asks with a "
                     "self-call — can the obligation be established for a normal, "
                     "regression-shaped input, or is the precondition too strong? — "
                     "takes a different form here, because the obligation quantifies "
                     "over all three booleans with NO hypothesis, so there is no "
                     "precondition to be too strong. What remains checkable, and is "
                     "checked here, is that the spec is genuinely SATISFIABLE at the "
                     "three regression-shaped points, rather than vacuous or "
                     "contradictory there: the containing-class-marked-only point "
                     "under the enabled option (the newly covered case), the "
                     "nothing-marked point under the enabled option (the case that "
                     "must keep deferring), and the option-disabled point. Each "
                     "`have` discharges the spec predicate applied to the "
                     "implementation's own output at that literal input, by "
                     "computation. If any of them could not be closed the spec would "
                     "be unsatisfiable at an in-domain input; the frozen proof then "
                     "follows unchanged, so the case also confirms the ground facts "
                     "cost the obligation nothing.",
    },

    # =====================================================================
    # UNIQUENESS (rivals) — each must NOT verify, and each carries a witness
    # confirmed by two real builds to hold of the rival and fail on gold.
    # =====================================================================

    # Ports nagini ATTACK 3 (partial-domain; the earlier behavior).
    {
        "id": "weak-drop-class-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let skipped := testItselfSkipped\n"
            "  if pdbEnabled && !skipped then\n"
            "    return true\n"
            "  return false"
        ),
        "witness": _w("true", "false", "true"),
        "rationale": "drops the containing class's marker from the combined "
                     "observation, keeping only the test's own. Correct on every "
                     "input where the class is not the sole marked party — which is "
                     "seven of the eight triples — and wrong exactly where the fix "
                     "bites: with the option enabled, the test's own marker clear "
                     "and the containing class's marker set, the spec's right-hand "
                     "side is false (the disjunction sees the class marker) while "
                     "this body returns true. The witness states the spec's negation "
                     "at that triple and closes by computation; it holds of this "
                     "rival and fails on the frozen solution, so the rejection is "
                     "attributable to the postcondition's disjunction and not to a "
                     "tactic mismatch.",
        "refinement": "this is the earlier behavior verbatim: consult only the "
                      "test's own skip marker when deciding whether the test is "
                      "going to run. Its faithful counterpart therefore still "
                      "intercepts and later replays the teardown step for a test "
                      "whose CONTAINING CLASS is marked skip, so that test's "
                      "teardown runs even though the test never ran. That is exactly "
                      "what the regression coverage added with the fix forbids — a "
                      "test in a class-marked-skip class, run with the interactive "
                      "debugger enabled, must record neither its setup nor its "
                      "teardown — so the faithful patch does NOT resolve. It is the "
                      "defect itself, so a verifying variant here would mean the "
                      "spec cannot see the bug.",
    },

    # Ports nagini ATTACK 4 (partial-domain, symmetric).
    {
        "id": "weak-drop-obj-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let skipped := classSkipped\n"
            "  if pdbEnabled && !skipped then\n"
            "    return true\n"
            "  return false"
        ),
        "witness": _w("true", "true", "false"),
        "rationale": "the mirror image of the previous rival: keeps the containing "
                     "class's marker and drops the test's own. It guards against a "
                     "spec that had pinned only the newly added half of the "
                     "disjunction and left the original half unconstrained — such a "
                     "spec would admit this body. Wrong with the option enabled, the "
                     "test's own marker set and its class's marker clear: the spec "
                     "pins false, the body returns true. The witness probes that "
                     "triple — a DIFFERENT point from the previous rival's, which "
                     "this body decides correctly — so the two cases demonstrate the "
                     "two disjuncts independently rather than sharing one point.",
        "refinement": "its faithful counterpart consults only the containing class's "
                      "marker, so a test whose OWN marker is set, inside a class "
                      "that is not marked, has its teardown step intercepted and "
                      "later replayed under the interactive debugger. The project's "
                      "pre-existing coverage for the individually-marked test "
                      "asserts that neither setup nor teardown is recorded in that "
                      "situation, for both marker spellings, so the faithful patch "
                      "regresses that coverage and does NOT resolve.",
    },

    # Ports nagini ATTACK 5 (wrong connective).
    {
        "id": "weak-and-connective",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let skipped := testItselfSkipped && classSkipped\n"
            "  if pdbEnabled && !skipped then\n"
            "    return true\n"
            "  return false"
        ),
        # Two points: this rival is wrong at BOTH single-marker triples, which
        # neither of the two preceding rivals is. The claim is therefore strictly
        # stronger than either of theirs and is demonstrated as such.
        "witness": _w("true", "true", "false") + "\n" + _w("true", "false", "true"),
        "rationale": "combines the two markers CONJUNCTIVELY where the spec demands "
                     "a disjunction, so a test counts as not-going-to-run only when "
                     "the test AND its containing class are both marked. This "
                     "attacks the decisiveness of each marker taken alone: the "
                     "spec's negation is provable at BOTH single-marker triples "
                     "under the enabled option, and the witness demonstrates both "
                     "rather than one. That is what distinguishes this case from the "
                     "two preceding rivals, each of which is correct at one of those "
                     "two points; sharing a single point with either would have left "
                     "this rival's broader claim undemonstrated. Note it is correct "
                     "when BOTH markers are set, so it is not subsumed by the "
                     "ignore-markers rival either.",
        "refinement": "its faithful counterpart treats a test as skipped only when "
                      "both the test and its containing class carry the marker, so "
                      "the ordinary single-marker cases — a marked test in an "
                      "unmarked class, and the newly covered unmarked test in a "
                      "marked class — both have their teardown step intercepted and "
                      "replayed under the interactive debugger. It therefore fails "
                      "the regression coverage added with the fix AND the "
                      "pre-existing individually-marked coverage, and does NOT "
                      "resolve.",
    },

    # Ports nagini ATTACK 6 (ignore the skip observation entirely).
    {
        "id": "weak-ignore-markers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("  return pdbEnabled"),
        "witness": _w("true", "true", "true"),
        "rationale": "returns the debugger-enabled option alone, discarding both "
                     "markers: defer whenever the debugger is enabled. This is the "
                     "'do none of the work' rival — it satisfies the necessity and "
                     "positive directions of the equality trivially and violates it "
                     "on every marked input under the enabled option. Its witness is "
                     "deliberately placed at the BOTH-markers-set triple, which each "
                     "of the three preceding rivals decides CORRECTLY — only the "
                     "decision-inverting rival below is also wrong there — so this "
                     "case contributes a distinct input point rather than re-probing "
                     "a single-marker one.",
        "refinement": "its faithful counterpart drops the whole "
                      "is-this-test-going-to-run condition and intercepts the "
                      "teardown step whenever the interactive debugger is enabled. "
                      "Every skipped test then has its teardown replayed — the newly "
                      "covered class-marked case and the pre-existing "
                      "individually-marked cases alike — so it fails both the added "
                      "and the pre-existing regression coverage and does NOT "
                      "resolve.",
    },

    # No nagini counterpart. Moves the FIRST binder, which every other witness
    # here holds enabled; without it a rival that mishandled only the disabled
    # option would verify unnoticed.
    {
        "id": "weak-ignore-pdb-option",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let skipped := testItselfSkipped || classSkipped\n"
            "  if !skipped then\n"
            "    return true\n"
            "  return false"
        ),
        "witness": _w("false", "false", "false"),
        "rationale": "keeps the combined marker observation exactly right and drops "
                     "the debugger-enabled conjunct, deferring for any live test "
                     "whether or not the debugger is enabled. It is wrong ONLY while "
                     "the option is disabled (at the all-clear triple), and its "
                     "witness is the only one that moves `pdbEnabled` to false — "
                     "without it every witness in the battery would hold that binder "
                     "at the same value, and a rival mishandling only the "
                     "option-disabled sub-domain (which is the common case in any "
                     "real run) would satisfy every probe the battery makes. The "
                     "spec pins false at the all-clear, option-disabled triple; this "
                     "body returns true.",
        "refinement": "its faithful counterpart intercepts the per-test teardown "
                      "step unconditionally rather than only when the interactive "
                      "debugger is enabled, which changes the moment at which every "
                      "ordinary test's teardown runs relative to the results "
                      "bookkeeping — deliberately avoided in the existing code. "
                      "Teardown ordering and failure reporting are asserted by the "
                      "project's pre-existing teardown coverage (teardown "
                      "observable by a later test, teardown-and-test both failing "
                      "reported as a failure plus an error, cleanup counts on "
                      "teardown failure), so the faithful patch regresses that "
                      "coverage and does NOT resolve.",
    },

    # No nagini counterpart. The only witness probing the single point at which
    # the spec demands the deferral — i.e. the positive direction.
    {
        "id": "weak-invert-decision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let skipped := testItselfSkipped || classSkipped\n"
            "  if pdbEnabled && !skipped then\n"
            "    return false\n"
            "  return true"
        ),
        "rationale": "computes the combined observation and the guard correctly and "
                     "then swaps the two exits, so it defers exactly when the spec "
                     "says not to. Its purpose is to attack the POSITIVE direction "
                     "of the equality — the requirement that a live test under the "
                     "enabled debugger MUST have its teardown step specially "
                     "deferred. The witness is therefore placed at the "
                     "option-enabled, neither-marker-set triple: the single point in "
                     "the eight-point domain where the spec demands `true`, and the "
                     "one point no other witness in this battery probes. A spec that "
                     "had only forbidden deferral (all the negative directions, none "
                     "of the positive one) would admit this body, and every other "
                     "rival here would still be caught — so without this case that "
                     "weakening would be invisible.",
        "witness": _w("true", "false", "false"),
        "refinement": "its faithful counterpart intercepts the teardown step for "
                      "precisely the tests that are not going to run and leaves it "
                      "alone for the live ones. The interception exists so that a "
                      "live test's teardown can be replayed after the debugger "
                      "prompt instead of before it; skipping it for live tests means "
                      "teardown is never deferred where it matters, while the "
                      "captured-teardown replay path fires for tests that never ran. "
                      "The project's pre-existing coverage asserts that teardown IS "
                      "eventually invoked, once per test, for live tests under the "
                      "interactive debugger, and that a live test's instance "
                      "attributes are still readable at the debugger prompt; both "
                      "regress, so the faithful patch does NOT resolve.",
    },

    # ADDED BY AUDIT. No nagini counterpart. The six rivals above leave the three
    # option-disabled MARKED triples unprobed, and the point-spread block used to
    # justify that by arguing no in-scope rival could be wrong only there. That
    # argument is false, and this case is the demonstration: the body below is
    # wrong at EXACTLY those three points and nowhere else, so without it the
    # battery's only defence of that sub-domain was the positives.
    {
        "id": "weak-xor-option-against-markers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "  let skipped := testItselfSkipped || classSkipped\n"
            "  if pdbEnabled != skipped then\n"
            "    return true\n"
            "  return false"
        ),
        "witness": (_w("false", "false", "true") + "\n"
                    + _w("false", "true", "false") + "\n"
                    + _w("false", "true", "true")),
        "rationale": "computes the combined marker observation exactly right and then "
                     "relates it to the debugger-enabled option by INEQUALITY instead "
                     "of by the spec's conjunction-with-negation: it defers when "
                     "exactly one of `the option is enabled` / `some marker is set` "
                     "holds. That agrees with the spec on all five triples every "
                     "other witness in this battery probes — including both "
                     "single-marker points, the both-markers point, the live point "
                     "and the all-clear disabled point — and is wrong ONLY at the "
                     "three option-disabled MARKED triples, which no other rival here "
                     "is wrong at. It exists because those three points were the "
                     "battery's blind spot: it demonstrates, rather than argues, that "
                     "the sub-domain needs its own probe, and that an in-consequence "
                     "wrong body confined to it does not have to ignore the markers "
                     "and the option together. The witness states the spec's negation "
                     "at all three of those triples and closes each by computation.",
        "refinement": "its faithful counterpart still decides the live-test case and "
                      "both individually-marked cases as the fix requires, so the "
                      "added and pre-existing skip coverage stays green; what it "
                      "breaks is the ordinary run with the interactive debugger NOT "
                      "enabled, where it starts intercepting and replaying the "
                      "per-test teardown of every skipped test even though nothing "
                      "asked for the debugger. The project's pre-existing coverage of "
                      "skip handling outside the debugger — teardown not running for "
                      "skipped unittest tests, and setup-inheritance skipping at the "
                      "test, class and module level — asserts that behavior, so the "
                      "faithful patch regresses it and does NOT resolve.",
    },
]


# ---------------------------------------------------------------------------
# POINT SPREAD of the reject witnesses (the coverage invariant the gate does NOT
# check). Triples are (pdbEnabled, testItselfSkipped, classSkipped):
#
#   weak-drop-class-skip     (true,  false, true )
#   weak-drop-obj-skip       (true,  true,  false)
#   weak-and-connective      (true,  true,  false) and (true, false, true)
#   weak-ignore-markers      (true,  true,  true )
#   weak-ignore-pdb-option   (false, false, false)
#   weak-invert-decision     (true,  false, false)
#   weak-xor-option-against-markers
#                            (false, false, true ), (false, true, false)
#                            and (false, true, true)
#
# ALL EIGHT points of the domain are now probed by some reject witness, and every
# one of the three binders takes BOTH values across the set. Counting DISTINCT
# points: pdbEnabled true at four, false at four; testItselfSkipped true at four,
# false at four; classSkipped true at four, false at four. No binder is held at
# one value by every witness, so no rival that mishandled a single input can slip
# through unprobed.
#
# AUDIT CORRECTION. This block previously recorded FIVE distinct points and
# justified the three unprobed option-disabled MARKED triples by arguing that a
# rival wrong only there "would have to ignore the markers AND the option, which
# `weak-ignore-markers` and `weak-ignore-pdb-option` already refute at points they
# do probe". That argument is FALSE, and the arithmetic it rested on was wrong too
# (it counted witness instances rather than distinct points, reporting pdbEnabled
# as true at five of five). `weak-xor-option-against-markers` is an in-scope rival
# that computes the marker disjunction exactly right, keeps the option, and is
# wrong at PRECISELY those three triples and nowhere else — so the sub-domain was
# genuinely undefended by the reject lane, not covered by inference. It is now
# probed directly, by three real builds.
# ---------------------------------------------------------------------------
