"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7571 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct <name>`` obligation survives with a byte-identical header)
and swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (FOUR contracted methods over a small retained-state carrier,
``FixtureState { level : Int, savedLevel : Option Int }``):

  initStep    (lvl0 : Int)              return (st  : FixtureState)
    ensures st  = initState lvl0                       -- construction
  setLevelStep (st : FixtureState) (lvl : Int) return (st' : FixtureState)
    ensures st' = setLevelState st lvl                 -- set-during-test
  restoreStep (st : FixtureState)       return (st' : FixtureState)
    ensures st' = restoreState st                      -- end-of-test cleanup
  runLifecycle (lvl0 : Int) (lvl : Int) return (out : FixtureState)
    ensures out = restoreState (setLevelState (initState lvl0) lvl)  -- composed
    ensures out.level = lvl0                           -- round trip

There is NO ``require`` on any method (the spec accepts every input) and the
``axioms`` region is empty — every ``ensures`` is pinned to a fully-unfolded pure
``def`` (``initState`` / ``setLevelState`` / ``restoreState``) over the method's
own arguments, so there is no opaque answer key a wrong impl could echo
(directive 8). The load-bearing structure, clause by clause:

  * initState    — a fresh state is at the ambient ``lvl0`` and records NOTHING
                   (``savedLevel = none``);
  * setLevelState — records the level in effect NOW (``some st.level``) and moves
                   to the requested ``lvl``; recording is UNCONDITIONAL (a plain
                   assignment, not a set-once), so ``savedLevel`` is ``some
                   st.level`` regardless of what it was;
  * restoreState — reinstates the recorded level on the ``some`` branch (``level
                   := v``) and is the IDENTITY on the ``none`` branch;
  * runLifecycle — the composed round trip: the level set during the test is
                   undone, so ``out.level`` is back at the ambient ``lvl0``.

INPUT BINDERS, all free: ``lvl0`` (initStep, runLifecycle), ``st`` (setLevelStep,
restoreStep — carrying both ``level`` and ``savedLevel``), ``lvl`` (setLevelStep,
runLifecycle). The reject witnesses vary every one of them (see the footer).

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case in the
footer):
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling already records this
    class as inapplicable (``set_level`` / ``teardown_restore`` take
    full-permission ``Acc`` on the fields they legitimately mutate; there is no
    ``Acc(x,1/2)`` read-only param and the driver's ints are pass-by-value).
    Lean/Velvet are referentially transparent a fortiori: every input is an
    immutable value, no method declares a ``mut`` binder, there is no heap and no
    aliasing. No substitute probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. Each ``ensures``
    is pinned to a concrete ``def`` over the method's own inputs (empty
    ``axioms`` region); there is nothing to echo. The positive controls are the
    honest cheapest-impl analogues.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``match`` / ``let`` over
    immutable values, no loop and no recursion), so there is no control flow
    here to make diverge: a diverging rival cannot be obtained by mutating this
    body, it has to bring a loop of its own. When it does, the semantics refuse
    it. This bundle sets ``loom.semantics.termination "total"`` AND carries
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
  * PARTIAL-DOMAIN / VALUE — carries the reject lane. Each rival gets the SHAPE
    right (same carrier, same branch structure) and is correct on part of the
    domain, diverging on one structural sub-behaviour of one ``ensures``.

AUDIT (independent, post-port). All 12 reject witnesses were rebuilt from the
manifest and checked against BOTH subjects with the real verifier: every one
elaborates against its rival (exit 0) and FAILS against the frozen solution
(exit 1), each gold-side failure being the SEMANTIC refutation ``Tactic `decide`
proved that the proposition <name>Tester <args> = false is false`` — a decided
verdict, not a missing identifier, a type error, or a stuck reduction. No witness
binds a hypothesis, so no consistency probe is required. Attacks D and E were run
with NEW impls the battery did not contain: four fresh wrong impls (a set-once
record, a level-preserving set, an init that seeds only at nonzero ambient, and a
lifecycle wrong only on negative ambient) were ALL rejected, and no spec hole was
found at the value level; three fresh correct reshapes were tried, of which the
two faithful ones verify (one is now shipped as ``pos-restore-getd-guard``) and
the two rejected candidates are observably DIFFERENT from the frozen behaviour,
not faithful (details in that case's rationale). The in-region admissibility
assert was confirmed LIVE by negating one conjunct: the variant then fails with
``decide`` reporting the conjunction false.

WITNESS MECHANICS. Every modeled impl is LOOP-FREE (``pure`` / ``match`` / a
straight-line ``do`` of the sub-steps), so each extracted tester — including the
COMPOSITE ``runLifecycleTester`` — reduces under ``decide`` (checked out-of-band:
all four testers ``decide`` to a Boolean on gold). Each reject rival is likewise
loop-free, so its tester ``decide``s too. Each reject case therefore carries a
machine-checked refutation ``witness`` — a Velvet tester statement
``<name>Tester <args> = false`` at ONE concrete input — checked in a file whose
``prove_correct`` blocks have been stripped so no tactic script can mask the
verdict. Both halves were checked with ``scripts/lean_verify.sh``: every witness
ELABORATES against its rival (the tester ``decide``s to ``false`` — the rival's
output violates the postcondition there) and FAILS against the frozen solution
(gold's tester ``decide``s to ``true``, so ``= false`` is refuted). No witness
binds a hypothesis (all inputs are concrete literals), so the consistency probe
is vacuous.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references;
the whole computation is concrete state arithmetic over the inputs. This gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7571"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the exact impl-region bodies, verbatim from Solution.lean. Each anchor
# ---- lies wholly inside one method's `-- impl-start` / `-- impl-end` region and
# ---- is unique in the file (both facts asserted at load). Every rival and
# ---- reshape edits ONLY these (and, where a reshape needs it, the elided
# ---- `prove_correct` tactic body), so the spec view is untouched and same_spec
# ---- holds by construction.
_INIT = "    pure { level := lvl0, savedLevel := none }"
_SET = "    pure { level := lvl, savedLevel := some st.level }"
_REST = ("    match st.savedLevel with\n"
         "    | some v => pure { st with level := v }\n"
         "    | none   => pure st")
_LIFE = ("    let st0 ← initStep lvl0\n"
         "    let st1 ← setLevelStep st0 lvl\n"
         "    let st2 ← restoreStep st1\n"
         "    return st2")

for _anchor in (_INIT, _SET, _REST, _LIFE):
    assert _BASE.count(_anchor) == 1, f"impl anchor drift: {_anchor[:40]!r}"

# ---- the runLifecycle proof, verbatim (tactic body only; elided from the spec
# ---- view). The admissibility case retunes ONLY this to clear the extra assert
# ---- goal, keeping the `prove_correct runLifecycle` header byte-identical.
_PROOF_LIFE = "prove_correct runLifecycle by\n  loom_solve"
assert _BASE.count(_PROOF_LIFE) == 1, "runLifecycle proof anchor drift"

# ---- the restoreStep proof, verbatim (tactic body only). The `getd-guard`
# ---- positive retunes ONLY this, because its reshaped guard is NOT
# ---- definitionally the frozen body and the frozen script does not close it;
# ---- the `prove_correct restoreStep` header stays byte-identical.
_PROOF_REST = "prove_correct restoreStep by\n  loom_solve <;> simp_all [restoreState]"
assert _BASE.count(_PROOF_REST) == 1, "restoreStep proof anchor drift"


def _impl(anchor, body):
    """Full Solution.lean variant with ONE method's impl body replaced."""
    return _swap(_BASE, anchor, body)


# ---- witness preamble. Each spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `<name>Tester <args> = false` says the extracted program's result violates
# ---- the method's postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` blocks have been stripped. Every argument is a concrete
# ---- literal so `decide` reduces the (loop-free) extracted program.
def _witness(method, call):
    return (f"extract_program_for {method}\n"
            f"prove_precondition_decidable_for {method}\n"
            f"prove_postcondition_decidable_for {method}\n"
            f"derive_tester_for {method}\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot satisfy the
    # postcondition, the spec is SPEC-TOO-STRONG.
    #
    # CALIBRATION (measured in the audit, not asserted): the first three below
    # are DEFINITIONALLY equal to the frozen body — `initState lvl0` and
    # `setLevelState st lvl` unfold to the frozen record literals, and a `match`
    # on `Option` compiles to the same `casesOn` under either arm order — so
    # each rides the frozen tactic script UNCHANGED and probes only that the
    # spec is not pinned to the literal SPELLING of the impl. That is worth
    # having (it is exactly the sibling's local-reshape/branch-reorder probe)
    # but it is a WEAK positive: it cannot detect a spec that is too strong
    # about behaviour, only one too strong about syntax. `pos-restore-getd-
    # guard` is the strong one — it is the only positive whose obligation the
    # frozen script does NOT close, so it is the only one that shows a correct
    # impl the spec was not tuned for is still admitted.
    # (Sibling: pos-setlevel-localreshape, pos-teardown-branch-reorder.)
    # =====================================================================
    {
        "id": "pos-init-direct",
        "kind": "soundness",
        "expect": "verify",
        # Return the grounded model directly instead of the inlined record
        # literal. `st` IS `initState lvl0`, so the ensures holds on the whole
        # domain; the frozen proof (`loom_solve <;> simp_all [initState]`) closes.
        "module": _impl(_INIT, "    pure (initState lvl0)"),
        "rationale": (
            "the cheapest honest correct impl for construction returns the "
            "grounded model `initState lvl0` directly rather than the inlined "
            "record literal. `st` IS that model, so `st = initState lvl0` holds "
            "everywhere; a faithful reshape MUST verify, else the postcondition "
            "is SPEC-TOO-STRONG (it would reject its own model's output)."),
    },
    {
        "id": "pos-setlevel-direct",
        "kind": "soundness",
        "expect": "verify",
        # Return the grounded model directly; observationally identical to the
        # inlined `{ level := lvl, savedLevel := some st.level }`.
        "module": _impl(_SET, "    pure (setLevelState st lvl)"),
        "rationale": (
            "the set-during-test step returns the grounded model "
            "`setLevelState st lvl` directly — the same record-then-move "
            "semantics in a different shape, so `st' = setLevelState st lvl` "
            "holds on the whole domain; MUST verify (else SPEC-TOO-STRONG). "
            "(Sibling: pos-setlevel-localreshape.)"),
    },
    {
        "id": "pos-restore-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch REORDER: handle the `none` (nothing recorded) arm first, restore
        # in the `some` arm. Same observable behaviour as the gold guard.
        "module": _impl(
            _REST,
            "    match st.savedLevel with\n"
            "    | none   => pure st\n"
            "    | some v => pure { st with level := v }"),
        "rationale": (
            "the end-of-test cleanup as a match with the `none` arm first "
            "reinstates exactly when a value was recorded and leaves the state "
            "untouched otherwise — the gold behaviour with reordered arms, so "
            "`st' = restoreState st` still holds; MUST verify (else "
            "SPEC-TOO-STRONG). (Sibling: pos-teardown-branch-reorder.)"),
    },

    {
        "id": "pos-restore-getd-guard",
        "kind": "soundness",
        "expect": "verify",
        # A reshape that is NOT definitionally the frozen body: the recorded
        # slot is tested with `Option.isSome` and read with `Option.getD`,
        # replacing the `match` that binds `v`. Measured during the audit: with
        # the frozen `restoreStep` proof tactic UNCHANGED this variant does NOT
        # elaborate (`unsolved goals`, ensures_1, with `if_pos :
        # st.savedLevel.isSome = true` and a residual `getD`-vs-`match` goal),
        # so the obligation genuinely has to be RE-PROVEN for the new shape —
        # unlike the three positives above, each of which is definitionally
        # equal to the frozen body and rides the frozen script unchanged. The
        # proof gains an `Option` case split (tactic body only; elided from the
        # spec view, `prove_correct restoreStep` header byte-identical).
        "module": _swap(
            _impl(
                _REST,
                "    if st.savedLevel.isSome then\n"
                "      pure { st with level := st.savedLevel.getD st.level }\n"
                "    else\n"
                "      pure st"),
            _PROOF_REST,
            "prove_correct restoreStep by\n"
            "  loom_solve <;> cases hs : st.savedLevel <;> simp_all [restoreState]"),
        "rationale": (
            "the end-of-test cleanup written with a Boolean `isSome` guard and a "
            "defaulting `getD` read instead of a value-binding `match` is the "
            "SAME function extensionally (`getD` on the `some` branch returns the "
            "recorded value; the `else` branch is reached only when nothing was "
            "recorded, where the spec is the identity) — so `st' = restoreState "
            "st` holds on the whole domain and it MUST verify, else the "
            "postcondition is SPEC-TOO-STRONG about the SHAPE of the guard "
            "rather than about behaviour. This is the battery's load-bearing "
            "positive: it is the only one whose obligation the frozen tactic "
            "script does not already close, so it is the only one that shows the "
            "spec admits a correct impl it was not tuned for. Two nearby "
            "reshapes were also tried during the audit and are recorded there, "
            "not here: an unguarded branchless `getD` (correct on the `some` "
            "branch but WRONG on `none`, where it rebuilds the record instead of "
            "returning `st`) and a variant that clears the recorded slot after "
            "reinstating (observably different — the spec pins `savedLevel` "
            "unchanged); both are legitimately rejected."),
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini sibling composes __init__ -> set_level ->
    # teardown_restore on the exact F2P numbers (ambient 0, raised to 41) and
    # asserts the post-teardown level is back at ambient. This backend has no
    # `require` on any method, so "a normal input satisfies the precondition" is
    # degenerate; the residual admissibility risk is that the composed post-image
    # is DEGENERATE at the F2P point. This case discharges an in-region `assert`,
    # at the exact F2P shape (lvl0 = 0, lvl = 41), that the round trip is
    # NON-DEGENERATE: after set-then-cleanup the level is back at 0 AND the
    # intermediate save actually recorded the ambient (savedLevel = some 0) AND
    # the no-set cleanup is the identity. The runLifecycle impl is kept verbatim
    # so the method's own obligation still discharges; the proof gains a `decide`
    # arm to clear the assert goal (elided from the spec view). The assert is
    # LIVE — a false claim leaves an unsolved goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-lifecycle",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _impl(
                _LIFE,
                "    let st0 ← initStep lvl0\n"
                "    let st1 ← setLevelStep st0 lvl\n"
                "    let st2 ← restoreStep st1\n"
                "    assert (with_name_prefix `admiss (\n"
                "      (restoreState (setLevelState (initState 0) 41)).level = 0 ∧\n"
                "      (setLevelState (initState 0) 41).savedLevel = some 0 ∧\n"
                "      (restoreState (initState 0)).level = 0))\n"
                "    return st2"),
            _PROOF_LIFE,
            "prove_correct runLifecycle by\n  loom_solve\n  all_goals decide"),
        "rationale": (
            "the composed post-image is satisfiable AND non-degenerate at the "
            "exact F2P shape (ambient 0 raised to 41): the set-then-cleanup round "
            "trip lands the level back at 0, the intermediate set records the "
            "ambient (`savedLevel = some 0`, the recorded-value clause), and the "
            "no-set cleanup is the identity — so the obligation is neither "
            "unsatisfiable nor a constant collapse. The in-region assert must "
            "discharge; the runLifecycle impl is kept verbatim so `out = "
            "restoreState (setLevelState (initState lvl0) lvl)` and `out.level = "
            "lvl0` still verify. (Sibling: admiss-f2p-lifecycle, re-aimed from "
            "precondition admissibility to post-image non-degeneracy.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Each rival is loop-free so
    # its extracted tester `decide`s; the frozen spec is untouched.
    # =====================================================================

    # ---- initStep: attacks `st = initState lvl0` (the ambient-level component).
    {
        "id": "weak-init-wrong-ambient",
        "kind": "uniqueness",
        "expect": "reject",
        # Construct the fresh state at the WRONG ambient (lvl0 + 1) — correct
        # savedLevel (none), wrong level.
        "module": _impl(_INIT, "    pure { level := lvl0 + 1, savedLevel := none }"),
        "refinement": (
            "a faithful counterpart that constructed the fixture at the wrong "
            "ambient level would report the wrong level on entry to every test — "
            "the entry check that a freshly-created fixture is at the ambient "
            "level (0) would observe an off-by-one level and fail immediately, so "
            "it does NOT resolve."),
        "rationale": (
            "REJECT from `st = initState lvl0`: `initState` pins the fresh level "
            "to `lvl0`, the rival returns `lvl0 + 1`, so the states disagree at "
            "every input. Verifying would be SPEC-TOO-WEAK (the ambient level "
            "unpinned). Refuted at lvl0 = 0: gold's state is {0, none}, the "
            "rival's {1, none}."),
        "witness": _witness("initStep", "initStepTester 0"),
    },
    {
        "id": "weak-init-savedseed",
        "kind": "uniqueness",
        "expect": "reject",
        # Construct at the correct ambient but SEED savedLevel with `some lvl0`
        # (a fresh state records nothing). Correct level, wrong savedLevel; a
        # distinct input point (lvl0 = 7) from weak-init-wrong-ambient.
        "module": _impl(_INIT, "    pure { level := lvl0, savedLevel := some lvl0 }"),
        "refinement": (
            "a faithful counterpart that pre-seeded the restore point at fixture "
            "creation would make the first end-of-test cleanup reinstate the "
            "seeded level even for a test that never set one — corrupting the "
            "level for the following test, whose entry check then fails. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from `st = initState lvl0` via the recorded-value component: "
            "`initState` fixes `savedLevel = none`, the rival seeds `some lvl0`, "
            "so the states disagree at every input. Verifying would be "
            "SPEC-TOO-WEAK (the fresh state's empty restore-point unpinned). "
            "Refuted at lvl0 = 7 (a DISTINCT input point from wrong-ambient's 0, "
            "so the two init rivals jointly exercise lvl0's dependence): gold's "
            "state is {7, none}, the rival's {7, some 7}."),
        "witness": _witness("initStep", "initStepTester 7"),
    },

    # ---- setLevelStep: attacks `st' = setLevelState st lvl`. Three rivals cover
    # ---- the recorded-value component (savedLevel = some st.level) and the
    # ---- moved-level component (level = lvl).
    {
        "id": "weak-setlevel-norecord",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch shape: move the level but record NOTHING (savedLevel
        # stays none). Correct level, missing the recorded restore point.
        "module": _impl(_SET, "    pure { level := lvl, savedLevel := none }"),
        "refinement": (
            "this is the pre-patch set-during-test (the level is moved but the "
            "level in effect is never recorded for reinstatement); the "
            "end-of-test cleanup then finds nothing to restore and leaves the "
            "level at the raised value — exactly the reported regression, so the "
            "test that checks the level is back to ambient in the NEXT test fails. "
            "Does NOT resolve. (Sibling: weak-setlevel-norecord-prepatch.)"),
        "rationale": (
            "REJECT from `st' = setLevelState st lvl` via the recorded-value "
            "clause: the spec records `some st.level`, the rival leaves "
            "`savedLevel = none`. Verifying would be SPEC-TOO-WEAK (the record is "
            "unpinned). Refuted at st = {7, none}, lvl = 42: gold saves `some 7`, "
            "the rival `none`. Discrimination comes from `st.level` (= 7)."),
        "witness": _witness(
            "setLevelStep",
            "setLevelStepTester { level := 7, savedLevel := none } 42"),
    },
    {
        "id": "weak-setlevel-record-new",
        "kind": "uniqueness",
        "expect": "reject",
        # Record the NEW requested level instead of the level in effect. Correct
        # whenever lvl == st.level; wrong otherwise.
        "module": _impl(_SET, "    pure { level := lvl, savedLevel := some lvl }"),
        "refinement": (
            "a faithful counterpart that recorded the REQUESTED level rather than "
            "the level in effect would reinstate the raised level at teardown "
            "instead of the ambient one; the next test would see the raised level "
            "rather than the ambient, so the restore check fails. Does NOT "
            "resolve. (Sibling: weak-setlevel-record-new-level.)"),
        "rationale": (
            "REJECT from `st' = setLevelState st lvl` via the recorded-value "
            "clause: the spec records `some st.level`, the rival records `some "
            "lvl`, equal only when lvl = st.level. Refuted at st = {3, none}, "
            "lvl = 41: gold saves `some 3`, the rival `some 41`. Discrimination "
            "comes from lvl differing from `st.level` (the near-miss the "
            "norecord rival does not subsume)."),
        "witness": _witness(
            "setLevelStep",
            "setLevelStepTester { level := 3, savedLevel := none } 41"),
    },
    {
        "id": "weak-setlevel-record-zero-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # Record the level in effect ONLY when it is non-zero; for a zero ambient
        # record nothing. Correct on every nonzero level, WRONG exactly at
        # st.level == 0 (the F2P ambient).
        "module": _impl(
            _SET,
            "    if st.level = 0 then pure { level := lvl, savedLevel := none }\n"
            "    else pure { level := lvl, savedLevel := some st.level }"),
        "refinement": (
            "a faithful counterpart that recorded the level in effect only when "
            "it is non-zero would NOT record the ambient 0 in the F2P scenario "
            "(the level in effect is 0, then it is raised); the end-of-test "
            "cleanup restores nothing and the next test sees the raised level "
            "rather than 0, so the restore check fails. Does NOT resolve. "
            "(Sibling: weak-setlevel-record-zero-skip.)"),
        "rationale": (
            "REJECT from `st' = setLevelState st lvl` via the recorded-value "
            "clause on the sub-domain st.level = 0: the spec records `some 0`, "
            "the rival records `none`. Refuted at st = {0, none}, lvl = 43: gold "
            "saves `some 0`, the rival `none`. Discrimination comes from the "
            "st.level = 0 sub-domain (which the other setlevel rivals, at nonzero "
            "st.level, agree with gold on) and from lvl = 43."),
        "witness": _witness(
            "setLevelStep",
            "setLevelStepTester { level := 0, savedLevel := none } 43"),
    },

    {
        "id": "weak-setlevel-nomove",
        "kind": "uniqueness",
        "expect": "reject",
        # Record the level in effect CORRECTLY but never actually move to the
        # requested `lvl`. Attacks the MOVED-LEVEL component (`level = lvl`),
        # which every other setLevelStep rival gets right — so no existing
        # witness refutes it. (Audit: added to close that gap.)
        "module": _impl(_SET, "    pure { level := st.level, savedLevel := some st.level }"),
        "refinement": (
            "a faithful counterpart that recorded the level in effect but never "
            "applied the requested one would leave the capture level unchanged "
            "for the duration of the test; the in-test check that the level IS "
            "the requested one (immediately after the set, before any cleanup) "
            "observes the old level and fails. Does NOT resolve."),
        "rationale": (
            "REJECT from `st' = setLevelState st lvl` via the MOVED-LEVEL "
            "component: the spec pins `level = lvl`, the rival leaves "
            "`level = st.level`, equal only when lvl = st.level. This is the one "
            "component of setLevelStep's obligation the other three rivals all "
            "satisfy (they each move the level correctly and break only the "
            "recorded value), so without this case `level = lvl` is attested by "
            "no witness. Refuted at st = {11, some 2}, lvl = 44: gold gives "
            "{44, some 11}, the rival {11, some 11}. Its `savedLevel = some 2` "
            "pre-state is also the first non-`none` incoming savedLevel among the "
            "setLevelStep witnesses."),
        "witness": _witness(
            "setLevelStep",
            "setLevelStepTester { level := 11, savedLevel := some 2 } 44"),
    },
    {
        "id": "weak-setlevel-record-once",
        "kind": "uniqueness",
        "expect": "reject",
        # Record ONLY if nothing is recorded yet (a set-once / setdefault
        # discipline) instead of the spec's UNCONDITIONAL overwrite. Correct on
        # every state whose savedLevel is `none` — i.e. on every FIRST set —
        # and wrong exactly on a second set within the same test.
        "module": _impl(
            _SET,
            "    match st.savedLevel with\n"
            "    | some v => pure { level := lvl, savedLevel := some v }\n"
            "    | none   => pure { level := lvl, savedLevel := some st.level }"),
        "refinement": (
            "a faithful counterpart that recorded the restore point only the "
            "first time a level is set within a test would, after two sets in "
            "one test, reinstate the level in effect before the FIRST set rather "
            "than before the second — the wrong restore target for the "
            "set-once discipline this state does NOT follow. It diverges from "
            "the real retained-level behaviour on every multi-set test, so it "
            "does NOT resolve."),
        "rationale": (
            "REJECT from `st' = setLevelState st lvl` via the "
            "UNCONDITIONALITY of the recording: the spec records `some st.level` "
            "regardless of the incoming `savedLevel` (a plain assignment, not a "
            "set-once), while the rival keeps an already-recorded value. The two "
            "agree on the whole `savedLevel = none` sub-domain, which is where "
            "EVERY other setLevelStep witness lives, so this rival is refuted by "
            "none of them: it is the only case that attests the "
            "unconditional-overwrite clause. Refuted at st = {5, some 9}, "
            "lvl = 30: gold gives {30, some 5}, the rival {30, some 9}."),
        "witness": _witness(
            "setLevelStep",
            "setLevelStepTester { level := 5, savedLevel := some 9 } 30"),
    },

    # ---- restoreStep: attacks `st' = restoreState st`. Three rivals cover the
    # ---- `some` branch (reinstate the recorded value) and the `none` branch
    # ---- (identity).
    {
        "id": "weak-restore-noop",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch shape: reinstate nothing (the bug). Leaves the level at
        # whatever it was, ignoring the recorded value.
        "module": _impl(_REST, "    pure st"),
        "refinement": (
            "this is the pre-patch end-of-test cleanup (no reinstatement of the "
            "recorded level); the level stays at the raised value after a test "
            "that set it, so the next test observes the raised level rather than "
            "the ambient — exactly the reported regression. Does NOT resolve "
            "(matches Solution_prepatch.lean / G-DIFF). (Sibling: "
            "weak-teardown-noop-prepatch.)"),
        "rationale": (
            "REJECT from `st' = restoreState st` via the `some` branch: when a "
            "value is recorded the spec reinstates it (`level := v`), the rival "
            "returns `st` unchanged. Verifying would be SPEC-TOO-WEAK (the "
            "reinstatement unenforced). Refuted at st = {41, some 0}: gold gives "
            "{0, some 0}, the rival {41, some 0}. Discrimination comes from "
            "`savedLevel = some _` with level differing from the recorded value."),
        "witness": _witness(
            "restoreStep",
            "restoreStepTester { level := 41, savedLevel := some 0 }"),
    },
    {
        "id": "weak-restore-offby1",
        "kind": "uniqueness",
        "expect": "reject",
        # Reinstate the recorded value PLUS ONE on the some branch. Picks the
        # right branch, restores to the wrong level by one.
        "module": _impl(
            _REST,
            "    match st.savedLevel with\n"
            "    | some v => pure { st with level := v + 1 }\n"
            "    | none   => pure st"),
        "refinement": (
            "a faithful counterpart that reinstated one past the recorded level "
            "would leave the level off by one after every test that set it; the "
            "next test would observe a level of 1 rather than the ambient 0, so "
            "the restore check (level back to ambient) fails. Does NOT resolve. "
            "Correct on every no-record test (a some-branch-value-only break)."),
        "rationale": (
            "REJECT from `st' = restoreState st` via the `some` branch value: the "
            "spec reinstates `v`, the rival `v + 1`. Refuted at st = {8, some 3}: "
            "gold gives {3, some 3}, the rival {4, some 3}. Distinct from the "
            "noop rival's input (this drives the recorded value to a nonzero 3 "
            "and the current level to 8), so it is not refuted by that witness."),
        "witness": _witness(
            "restoreStep",
            "restoreStepTester { level := 8, savedLevel := some 3 }"),
    },
    {
        "id": "weak-restore-none-bump",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupt the level on the NONE branch (should be the identity). Correct
        # on every some branch; wrong exactly when nothing was recorded.
        "module": _impl(
            _REST,
            "    match st.savedLevel with\n"
            "    | some v => pure { st with level := v }\n"
            "    | none   => pure { st with level := st.level + 1 }"),
        "refinement": (
            "a faithful counterpart that changed the level at teardown even when "
            "nothing was recorded would corrupt the level of any test that never "
            "set one — the cleanup, meant to be a no-op there, would push the "
            "level off by one and leak that into the following test's entry "
            "check, which fails. Does NOT resolve. Correct on every test that DID "
            "record a level (a none-branch-only break)."),
        "rationale": (
            "REJECT from `st' = restoreState st` via the `none` branch: when "
            "nothing is recorded the spec is the identity, the rival bumps the "
            "level. Verifying would be SPEC-TOO-WEAK (the no-op-when-nothing-"
            "recorded clause unpinned). Refuted at st = {5, none}: gold gives "
            "{5, none}, the rival {6, none}. Discrimination comes from `savedLevel "
            "= none` — the sub-domain the some-branch rivals agree with gold on."),
        "witness": _witness(
            "restoreStep",
            "restoreStepTester { level := 5, savedLevel := none }"),
    },

    # ---- runLifecycle: attacks the two independent `ensures` clauses of the
    # ---- composed round trip separately.
    {
        "id": "weak-lifecycle-skip-restore",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the end-of-test cleanup entirely (the composed pre-patch bug):
        # return the state right after the set, so the level is left raised.
        "module": _impl(
            _LIFE,
            "    let st0 ← initStep lvl0\n"
            "    let st1 ← setLevelStep st0 lvl\n"
            "    return st1"),
        "refinement": (
            "this is the composed pre-patch lifecycle with no end-of-test "
            "reinstatement; the level is left at the raised `lvl` after the "
            "test, so a subsequent test sees the raised level rather than the "
            "ambient — the exact reported regression. Does NOT resolve."),
        "rationale": (
            "REJECT from `out.level = lvl0`: without the cleanup step the level "
            "is left at `lvl`, which equals `lvl0` only when nothing was raised. "
            "Verifying would be SPEC-TOO-WEAK (the composed round trip "
            "unenforced). Refuted at lvl0 = 5, lvl = 99: gold's out.level is 5, "
            "the rival's 99. Attacks the round-trip clause `out.level = lvl0`; "
            "its `lvl = 99` differs from skip-set's `lvl = 41`, so the pair "
            "exercises runLifecycle's dependence on `lvl`."),
        "witness": _witness("runLifecycle", "runLifecycleTester 5 99"),
    },
    {
        "id": "weak-lifecycle-skip-set",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the set-during-test step: init then straight to cleanup. The level
        # ends at lvl0 (so `out.level = lvl0` still holds!), but the composed
        # state is `initState lvl0`, not `restoreState (setLevelState ...)` — it
        # attacks the STRUCTURAL clause, which the level clause alone would miss.
        "module": _impl(
            _LIFE,
            "    let st0 ← initStep lvl0\n"
            "    let st2 ← restoreStep st0\n"
            "    return st2"),
        "refinement": (
            "a faithful counterpart that skipped setting the level during the "
            "test would never raise the level at all; the test that requires the "
            "level to be raised WHILE it runs (before teardown) would observe the "
            "ambient level instead of the raised one and fail. Does NOT resolve. "
            "(Distinct from skip-restore: the final level still equals the "
            "ambient, so only the structural composed-state clause catches it.)"),
        "rationale": (
            "REJECT from `out = restoreState (setLevelState (initState lvl0) "
            "lvl)`: skipping the set makes `out = restoreState (initState lvl0)` "
            "= `initState lvl0`, whose `savedLevel` is `none`, whereas the spec's "
            "composed state records `some lvl0`. Note `out.level = lvl0` STILL "
            "holds, so this rival is caught ONLY by the structural clause — "
            "demonstrating that clause is load-bearing beyond the level clause. "
            "Refuted at lvl0 = 0, lvl = 41: gold's out is {0, some 0}, the "
            "rival's {0, none}."),
        "witness": _witness("runLifecycle", "runLifecycleTester 0 41"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling ships 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus an EMPTY AXIOM lane
# (AXIOM_TESTS = []). It contracts FOUR functions — __init__, set_level,
# teardown_restore, and an end-to-end driver — over a mutable CaptureController
# with integer fields. This backend models the SAME four code-paths DEEPLY and
# CONCRETELY (initStep / setLevelStep / restoreStep / runLifecycle over the
# `FixtureState { level : Int, savedLevel : Option Int }` carrier) with one
# `ensures` per method pinned to a pure `def`. The value surface carries across
# intact; there is no permission surface on either side.
#
#   sibling case                     kind          -> here                          disposition
#   -----------------------------------------------------------------------------------------
#   pos-setlevel-localreshape        soundness     -> pos-setlevel-direct           RE-SHAPED
#   pos-teardown-branch-reorder      soundness     -> pos-restore-branch-reorder    PORTED
#   (no sibling)                     soundness     -> pos-init-direct               ADDED
#   (no sibling)                     soundness     -> pos-restore-getd-guard        ADDED (audit)
#   admiss-f2p-lifecycle             admissibility -> admiss-f2p-lifecycle          RE-AIMED
#   weak-setlevel-record-zero-skip   uniqueness    -> weak-setlevel-record-zero-skip PORTED
#   weak-setlevel-record-new-level   uniqueness    -> weak-setlevel-record-new      PORTED
#   weak-setlevel-norecord-prepatch  uniqueness    -> weak-setlevel-norecord        PORTED
#   weak-teardown-noop-prepatch      uniqueness    -> weak-restore-noop             PORTED
#   weak-teardown-restore-to-zero    uniqueness    -> (none)                        DROPPED (refinement)
#   weak-teardown-always-restore     uniqueness    -> weak-restore-none-bump        RE-SHAPED
#   (no sibling)                     uniqueness    -> weak-init-wrong-ambient       ADDED
#   (no sibling)                     uniqueness    -> weak-init-savedseed           ADDED
#   (no sibling)                     uniqueness    -> weak-restore-offby1           ADDED
#   (no sibling)                     uniqueness    -> weak-lifecycle-skip-restore   ADDED
#   (no sibling)                     uniqueness    -> weak-lifecycle-skip-set       ADDED
#   (no sibling)                     uniqueness    -> weak-setlevel-nomove          ADDED (audit)
#   (no sibling)                     uniqueness    -> weak-setlevel-record-once     ADDED (audit)
#   AXIOM_TESTS ([])                 axiom         -> (none)                        N/A (G-AX)
#   frame-mutation                   (none)        -> (none)                        VACUOUS
#   divergence / non-termination     (none)        -> (none)                        VACUOUS (lean-family)
#
# ALL portable nagini cases ported (2 positives, 1 admissibility, 5 of 6
# uniqueness rivals); 1 uniqueness DROPPED for an honest-refinement reason (NOT
# for inexpressibility — see below); 8 rivals + 2 positives ADDED to
# defend/attack obligations the nagini carrier did not separate, 2 rivals and 1
# positive of those added by the adversarial audit to close measured gaps.
#
# RE-SHAPED / PORTED (positives): the sibling's set_level local-reshape becomes a
#   direct return of the grounded model `setLevelState st lvl` (pos-setlevel-
#   direct); its teardown branch-reorder ports directly (pos-restore-branch-
#   reorder). pos-init-direct is ADDED so the fourth obligation initStep is
#   DEFENDED by a structurally-different correct impl (the sibling folded
#   __init__ into the driver and did not defend it in isolation).
# RE-AIMED (admiss-f2p-lifecycle): the sibling asserts the post-teardown level is
#   back at ambient on the F2P numbers, demonstrating the call-site preconditions
#   admit a normal lifecycle. This backend has NO `require`, so that probe is
#   degenerate; the case is re-aimed to a live in-region assert that the composed
#   post-image is NON-DEGENERATE at the exact F2P shape (round trip to 0, the
#   intermediate save records the ambient, the no-set cleanup is the identity).
# PORTED (uniqueness): the three set_level rivals port directly to the recorded-
#   value / moved-level components of `setLevelState`; teardown-noop-prepatch
#   ports to restore-noop (the `some`-branch reinstatement). teardown-always-
#   restore (unconditional restore, which in nagini fails the no-op clause AND
#   passes None to a typed int field) RE-SHAPES to weak-restore-none-bump: on
#   this total, referentially-transparent carrier there is no partial-int type
#   error to trigger, so the faithful counterpart is expressed as corrupting the
#   level on the `none` branch — the same no-op-when-nothing-recorded clause the
#   sibling attacked, refuted on the `savedLevel = none` sub-domain.
# DROPPED (weak-teardown-restore-to-zero): the sibling restores to NOTSET(0)
#   whenever a value was recorded, and leans on a nonzero-ambient G-AX fuzz for
#   its non-resolution argument. It is EXPRESSIBLE here and it DOES discriminate
#   — re-derived in the audit, not assumed: the rival `| some _ => pure { st with
#   level := 0 }` is rejected (`unsolved goals`, ensures_1, residual `0 = i` under
#   `st.savedLevel = some i`) and the witness `restoreStepTester { level := 9,
#   savedLevel := some 3 } = false` elaborates against it (exit 0) while `decide`
#   refutes it on the frozen solution (exit 1). So the drop is NOT an
#   inexpressibility claim.
#   It stays dropped on the REFINEMENT ground only, and that ground is narrow:
#   the observable tested domain here creates the fixture at the ambient level 0
#   and asserts entry at 0, so "restore to 0" and "restore to the recorded value"
#   coincide on every input the harness drives — a faithful restore-to-0 patch
#   would RESOLVE, so the case cannot honestly claim non-resolution, which is what
#   an `expect="reject"` refinement field must assert. Shipping it would ship a
#   true `rationale` next to a false `refinement`.
#   Its `some`-branch-value coverage is carried by weak-restore-offby1 (v+1 breaks
#   the next test's entry check: level 1, not 0), whose refinement IS honest.
# ADDED (weak-restore-offby1, weak-lifecycle-skip-restore, weak-lifecycle-skip-
#   set, weak-init-wrong-ambient, weak-init-savedseed): the Lean-family bundle
#   contracts each code-path as its OWN obligation (the sibling folded them into
#   fewer functions), so each obligation is separately defended and attacked.
#   skip-restore attacks the composed `out.level = lvl0` clause (the literal
#   regression); skip-set attacks the INDEPENDENT structural clause `out =
#   restoreState (setLevelState ...)` that the level clause alone would miss;
#   init-wrong-ambient attacks the construction obligation's level component and
#   init-savedseed its recorded-value component (at a distinct lvl0), so the two
#   jointly exercise the construction obligation's dependence on lvl0.
# VACUOUS (frame-mutation): the sibling already records this class as
#   inapplicable (full-permission mutable fields, no read-only param). This
#   backend is referentially transparent and declares no `mut` binder — every
#   input is an immutable value with no heap footprint — so there is no read-only
#   field to overwrite and no substitute probe. Not fabricated.
# INEXPRESSIBLE-BECAUSE-ADMITTED (divergence / non-termination): the sibling
#   carries no diverge-*/nonterm-* case, so nothing is dropped in the port. But
#   the earlier reason recorded here ("a non-terminating impl cannot be written;
#   no `partial` semantics here") was WRONG on its first count and is corrected
#   below. But a SECOND revision then replaced it with something wrong in the
#   opposite direction, and that is RETRACTED IN FULL: it said this bundle DOES set
#   `loom.semantics.termination "partial"`, that under partial correctness a
#   diverging impl satisfies every `ensures` vacuously and VERIFIES, that the class
#   is therefore unshippable because the SPEC ADMITS the rival, and that this was
#   measured corpus-wide over a `partial` cohort and escalated in an internal
#   findings doc. Line 4 reads "total", as it does in all 500 velvet bundles, and
#   the option cannot drift from the file's `open TotalCorrectness` because the
#   `set_option` elaborator itself runs `openScope `TotalCorrectness`
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`). The cohort has no referent and
#   the doc no longer exists.
#   What IS true: a rival is free to INTRODUCE a loop the frozen impl never had, so
#   the class is not unwritable. Under `total` a postcondition is claimed of ALL
#   runs, so every such loop owes a strictly decreasing measure and the rival is
#   REJECTED. Measured on THIS bundle, proofs reduced to a bare `loom_solve`: an
#   unmeasured spun loop is refused at elaboration (`Decreasing annotations are
#   required in total correctness semantics`), and the sharper shape that CARRIES a
#   measure the body never shrinks (`while q > 0 / invariant 0 <= q /
#   done_with q = 0 / decreasing q`, body `q := q`) is rejected on the measure's own
#   goal, `case «decreasing_1: q»` with residual `q < q` unsolved. Nothing ships as
#   a reject case only because the refusal fires at the `method`, ahead of any
#   appended tester, so no witness can ELABORATE against the rival. No hole open.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   axioms and no deep-model references (the four code-paths are modeled
#   concretely, validated by G-CONF), so there is nothing to probe and the gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (12 rivals, 12 distinct input
# points). Corrected by the audit: the pre-audit footer claimed setLevelStep's
# "both components attacked", but all three original setLevelStep rivals moved the
# level CORRECTLY and broke only the recorded value, so the moved-level component
# `level = lvl` was attested by no witness; and all three sat on the
# `savedLevel = none` sub-domain, so the recording's UNCONDITIONALITY (the clause
# that distinguishes this state's plain assignment from a set-once discipline, and
# the one the sibling's modeling note calls out) was attested by none either. Two
# rivals were added for exactly those two clauses.
#   * initStep `st = initState lvl0`: lvl0 varied (0, 7). Attacked by
#     weak-init-wrong-ambient (level component, lvl0 = 0) and weak-init-savedseed
#     (recorded-value component, lvl0 = 7) — two distinct input points.
#   * setLevelStep `st' = setLevelState st lvl`: st.level varied (7, 3, 0, 11, 5),
#     lvl varied (42, 41, 43, 44, 30), incoming savedLevel ranges over none AND
#     some (some 2, some 9). ALL THREE clauses attacked — the moved level
#     (nomove: level := st.level, refuted at lvl != st.level); the recorded VALUE
#     (norecord: none vs some; record-new: some lvl vs some st.level; zero-skip:
#     none vs some 0 on the st.level = 0 sub-domain); and the recording's
#     unconditionality (record-once: keeps an already-recorded value, refuted only
#     on the savedLevel = some _ sub-domain, where every other rival agrees with
#     gold).
#   * restoreStep `st' = restoreState st`: st varied ({41,some 0}, {8,some 3},
#     {5,none}), savedLevel ranges over none/some. Both match branches attacked —
#     `some` value (noop, offby1) and `none` identity (none-bump).
#   * runLifecycle: lvl0 varied (5, 0), lvl varied (99, 41). BOTH `ensures`
#     clauses attacked — `out.level = lvl0` (skip-restore) and the structural
#     `out = restoreState
#     (setLevelState (initState lvl0) lvl)` (skip-set, which holds the level
#     clause and is caught only by the structural one).
#   No binder is pinned to a single value across the reject witnesses of the
#   obligation it belongs to; no two rivals share an input tuple.
AXIOM_TESTS = []
