"""properties.py — G-PBT falsification battery for django__django-13809 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct runStartupChecks`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. One contracted method that gates a startup-time routine's two
outwardly-observable effects — a progress announcement and the invocation of a
check routine — on a single read-only request flag:

  runStartupChecks (skipChecks : Bool) (mut announced : Bool) (mut checked : Bool)
      return (unit : Unit)
    require announced = false          -- entry: neither effect has happened yet
    require checked   = false
    ensures announced = (!skipChecks)  -- (C1) the announcement occurs iff not skipped
    ensures checked   = (!skipChecks)  -- (C2) the check invocation occurs iff not skipped

``skipChecks`` is the read-only request flag (not ``mut`` — directive 5).
``announced`` and ``checked`` are the two effect observables: each modeled as a
boolean occurrence flag (true iff that effect fired on this invocation), both
required false on entry and written by the routine. The two ``ensures`` clauses
are INDEPENDENT top-level clauses — the effects are governed together by the one
flag, but each observable is pinned by its own equation, so a rival can violate
exactly one.

BINDER STRUCTURE (read this before judging binder coverage). The postcondition's
only FREE input binder is ``skipChecks`` (Bool). The other two binders
(``announced``, ``checked``) are ``mut`` observables PINNED to ``false`` on entry
by the ``require`` clauses, so ``false`` is their only admitted value — a witness
holding them at ``false`` is not a pinned-binder gap but the only in-domain state
(the F2P test resets to that fresh state per invocation, mapping.md §2). The
reject witnesses therefore vary the single free binder ``skipChecks`` across BOTH
of its values ({true, false}) — the entire two-point input domain — and attack
each of the two clauses independently AT EACH of those values (the full
2-clause x 2-corner matrix; see the CLAUSE / BINDER COVERAGE note in the footer).

ADVERSARIAL READ of the nagini classes on THIS carrier (see the footer for the
case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS, exactly as the nagini sibling already
    reasoned (its only input is a primitive ``bool`` passed by value; there is no
    ``Acc(x,1/2)`` read-only reference to overwrite). Lean/Velvet are
    referentially transparent a fortiori: ``skipChecks`` is an immutable value and
    the two ``mut`` observables are pinned outputs, not aliased heap. No substitute
    probe is fabricated (per the porting map, this class is legitimately dropped).
  * UNGROUNDED-ORACLE ECHO — N/A. Both clauses equate an observable to a boolean
    function (``!skipChecks``) of the method's OWN input; the ``axioms`` region is
    empty, there is no opaque answer-key to echo (directive 8).
  * PARTIAL-DOMAIN / VALUE — APPLIES. The input domain is the two points
    {skip, no-skip}; every uniqueness attack is a partial-domain divergence
    (correct on one flag value, wrong on the other), refuted at the flag value
    where it diverges.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``if`` over immutable values, no loop and
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

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery. For a method
with ``mut`` observables the tester takes the method's parameters INCLUDING the
initial values of the ``mut`` binders: ``runStartupChecksTester skipChecks
announcedInit checkedInit = false`` says the extracted program's post-state
(the mutated observables) violates a ``require``/``ensures`` clause at that
concrete input. Each witness fixes the two ``mut`` inits to ``false`` (the only
value the ``require`` clauses admit, so no witness is vacuously excluded on a
false precondition). It is checked in a file whose ``prove_correct`` block has
been stripped, so no tactic script can mask the verdict. ``Bool`` has native
``DecidableEq``, so every witness closes by ``decide``. Both halves were checked
out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES against its
rival (tester ``decide``s to ``false``) and FAILS against the frozen solution
(gold's tester ``decide``s to ``true``, so ``= false`` is refuted by ``decide``),
so each rejection is a genuine spec refutation and not mechanical tactic breakage.
The gold-side failure text was READ, not just its exit code: each one is
``Tactic `decide` proved that the proposition ... is false`` — a semantic
refutation of the concrete claim, not a missing identifier, a type error, an
unfolding failure, or a timeout (any of which would make the witness a
non-discriminator the gate could not distinguish).

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references;
the two effects are modeled DIRECTLY as boolean occurrence flags (no callee
contract is consumed). Nothing in the proof rests on an axiom, and this gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13809"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap). It spans
# ---- the gold impl's leading comment and its guarded control flow, so a variant
# ---- replaces the entire behaviour (comment included) with no stale narration.
_GOLD_IMPL = (
    "    -- Perform the checks (emit the announcement, then invoke the check routine)\n"
    "    -- only when the operator has not requested that they be skipped; otherwise\n"
    "    -- leave both effect observables untouched.\n"
    "    if !skipChecks then\n"
    "      announced := true\n"
    "      checked := true\n"
    "      return ()\n"
    "    else\n"
    "      return ()"
)

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header is kept), so a case that adds an
# ---- in-region `assert` may retune its tactic script without touching the spec
# ---- statement or dropping the obligation. Unique in the file. (Every case in
# ---- this battery in fact keeps the frozen `loom_solve` verbatim — the positives
# ---- and the admissibility assert all discharge under it, verified out-of-band.)
_GOLD_PROOF = "prove_correct runStartupChecks by\n  loom_solve"

assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped. The
# ---- observables are `Bool` (native `DecidableEq`), so no instance needs
# ---- deriving and no assumption is introduced (`axiom`/`sorry`/`native_decide`
# ---- are absent); the frozen solution rejects these witnesses all the same.
def _tester(body):
    return (
        "extract_program_for runStartupChecks\n"
        "prove_precondition_decidable_for runStartupChecks\n"
        "prove_postcondition_decidable_for runStartupChecks\n"
        "derive_tester_for runStartupChecks\n\n" + body
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else the spec is SPEC-TOO-STRONG on impl shape.
    # The gold body handles the no-skip case in the `if` and leaves the skip
    # case to the `else`; this reshape INVERTS the branch (skip case in the
    # `if`, no-skip case in the `else`). Observationally identical post-state on
    # every input, no new proof obligation, so the frozen `loom_solve` discharges
    # the byte-identical obligation. Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-branch-invert",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Branch-inverted: handle the skip request in the `if` (leave both\n"
            "    -- observables untouched) and perform both effects in the `else`.\n"
            "    if skipChecks then\n"
            "      return ()\n"
            "    else\n"
            "      announced := true\n"
            "      checked := true\n"
            "      return ()"),
        "rationale": (
            "structurally different CORRECT reshape: the guard is inverted (skip "
            "handled in the `if`, no-skip in the `else`), which writes both "
            "observables to exactly `!skipChecks` on every input just as gold does. "
            "Both `ensures` clauses hold on the whole domain and no new obligation "
            "is generated, so the frozen `loom_solve` still closes the "
            "byte-identical obligation. A faithful reshape MUST verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — a second structurally different CORRECT
    # impl: assign each observable DIRECTLY from the boolean expression
    # `!skipChecks` instead of writing `true` inside a guarded branch. A
    # branch-free shape the gold impl does not contain; same post-state on every
    # input. Must verify, else SPEC-TOO-STRONG. Verified out-of-band.
    # =====================================================================
    {
        "id": "pos-direct-assign",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Branch-free: set each observable directly to whether the checks\n"
            "    -- are to be performed (the negation of the request flag).\n"
            "    announced := !skipChecks\n"
            "    checked := !skipChecks\n"
            "    return ()"),
        "rationale": (
            "structurally different CORRECT impl: a BRANCH-FREE assignment of each "
            "observable to `!skipChecks` (no `if`, no literal `true`), a term shape "
            "the gold impl does not contain, yet computing the same post-state on "
            "every input. Both clauses hold on the whole domain; the frozen "
            "`loom_solve` closes it. Must verify, else SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the precondition (`announced = false ∧ checked = false`)
    # must admit the F2P-shaped inputs AND the reachable post-state must be
    # non-degenerate (it distinguishes the two request-flag corners rather than
    # collapsing to a constant). The impl is the gold body with one `assert`
    # placed INSIDE EACH branch, so each assertion is discharged in the
    # branch's own reachable state: the goal carries the `require` hypotheses
    # (`announcedOld = false`, `checkedOld = false`), the branch condition, and
    # the writes performed so far, and it names the actual observables and the
    # actual free binder. In the checks-performed branch the state must satisfy
    # `announced = !skipChecks ∧ checked = !skipChecks ∧ announced = true`; in
    # the skip branch the same equations must hold with `announced = false`. So
    # the two corners are pinned to DIFFERENT reachable states, which is what
    # makes the case non-degenerate.
    #
    # AUDIT NOTE (repair). The previous version of this case asserted the CLOSED
    # Bool tautology `((!true) = false) ∧ ((!false) = true)`. That formula
    # mentions neither the observables nor `skipChecks` nor the contract, and it
    # elaborates by `decide` in a file containing no method at all — so it
    # demonstrated nothing about this precondition and the case's stated claim
    # ("the require clauses admit the F2P state") was unearned even though the
    # case honestly verified. The branch-local form below is load-bearing, and
    # measured to be: flipping either asserted corner to the wrong polarity
    # (claiming `announced = true` in the skip branch, or `announced = false` in
    # the checks-performed branch) makes the build FAIL with `unsolved goals`
    # showing `require_1/require_2` and `if_neg` in context — i.e. these
    # assertions are decided by the entry state and the branch, not by `decide`
    # on a constant.
    # =====================================================================
    {
        "id": "admiss-both-corners",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    -- Each branch asserts the pinned post-image IN ITS OWN reachable\n"
            "    -- state (entry `require`s + branch condition + writes so far), naming\n"
            "    -- the real observables and the real request flag. The two corners are\n"
            "    -- pinned to different states, so the post-image is non-degenerate.\n"
            "    if !skipChecks then\n"
            "      announced := true\n"
            "      checked := true\n"
            "      assert (with_name_prefix `assert\n"
            "        (announced = (!skipChecks) ∧ checked = (!skipChecks)\n"
            "          ∧ announced = true))\n"
            "      return ()\n"
            "    else\n"
            "      assert (with_name_prefix `assert\n"
            "        (announced = (!skipChecks) ∧ checked = (!skipChecks)\n"
            "          ∧ announced = false))\n"
            "      return ()"),
        "rationale": (
            "the entry-state precondition admits the F2P-shaped inputs and the "
            "REACHABLE post-image is non-degenerate. Each branch discharges an "
            "assert stated over the actual observables and the actual free binder "
            "in that branch's reachable state: where the checks are performed, "
            "`announced = !skipChecks ∧ checked = !skipChecks ∧ announced = true`; "
            "under a skip request, the same equations with `announced = false`. The "
            "two corners are therefore pinned to DIFFERENT states, so the "
            "post-image cannot be a collapsed constant. Each assert is decided by "
            "the `require` hypotheses plus the branch condition (measured: negating "
            "either corner's polarity fails with `unsolved goals` carrying "
            "`require_1`/`require_2`/`if_neg`), so if the require clauses could not "
            "admit a normal input the case would not verify => PRECOND-TOO-STRONG. "
            "The gold control flow and both writes are unchanged, so the method's "
            "own obligation still discharges under the frozen `loom_solve`."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. The input domain is the two
    # points {skip=true, skip=false}; the witnesses cover both.
    # =====================================================================
    {
        "id": "weak-skip-not-honored",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug (= Solution_prepatch skeleton). Perform BOTH effects
        # unconditionally, consulting no request flag. Violates BOTH clauses under
        # a skip request. Attacks (C1) and (C2) jointly.
        "module": _impl(
            "    -- Perform both effects unconditionally: consult no request flag.\n"
            "    announced := true\n"
            "    checked := true\n"
            "    return ()"),
        "refinement": (
            "this IS the pre-fix behaviour: the announcement is emitted and the "
            "check routine invoked on every startup, with no request-flag guard. "
            "The FAIL_TO_PASS test invokes the command with the skip request set "
            "and asserts the 'Performing system checks...' message is ABSENT and the "
            "check routine is NOT called; an ungated impl emits the message and "
            "calls the routine, so the test FAILS. A verifying rival here would be a "
            "true verify-does-not-resolve break."
        ),
        "rationale": (
            "REJECT from BOTH clauses (C1) `announced = (!skipChecks)` and (C2) "
            "`checked = (!skipChecks)`: under a skip request the post-image demands "
            "both observables false, but the rival sets both true. Refuted at "
            "skipChecks=true (mut inits false): both observables end true where the "
            "spec forces false, so the tester is false there while gold's is true."
        ),
        "witness": _tester(
            "example : runStartupChecksTester true false false = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-check-under-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # Guard only the announcement; invoke the check routine unconditionally.
        # (C1) announced holds, (C2) checked is violated under a skip request.
        # Isolates the `checked` clause.
        "module": _impl(
            "    -- Gate ONLY the announcement on the request flag; invoke the check\n"
            "    -- routine regardless of whether a skip was requested.\n"
            "    if !skipChecks then\n"
            "      announced := true\n"
            "      checked := true\n"
            "      return ()\n"
            "    else\n"
            "      checked := true\n"
            "      return ()"),
        "refinement": (
            "a faithful counterpart guards ONLY the progress announcement by the "
            "request flag but leaves the check-routine invocation OUTSIDE the guard, "
            "so the checks still run under a skip request — only the banner is "
            "hidden. The FAIL_TO_PASS test asserts the check routine is NOT called "
            "when the skip is requested, so it FAILS: the point of the change is to "
            "SKIP the checks, not merely to suppress their announcement. It would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from (C2) `checked = (!skipChecks)`: under a skip request the "
            "post-image demands `checked` false, but the rival invokes the check "
            "unconditionally, leaving `checked` true. (C1) `announced` is correct "
            "here, so this rival isolates the checked clause. Refuted at "
            "skipChecks=true (mut inits false)."
        ),
        "witness": _tester(
            "example : runStartupChecksTester true false false = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-announce-under-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # The DUAL: guard only the check invocation; emit the announcement
        # unconditionally. (C2) checked holds, (C1) announced is violated under a
        # skip request. Isolates the `announced` clause — the carrier splits the
        # single nagini schedule observable into two independent boolean clauses,
        # so each needs a rival that isolates it.
        "module": _impl(
            "    -- Gate ONLY the check-routine invocation on the request flag; emit\n"
            "    -- the progress announcement regardless of the skip request.\n"
            "    if !skipChecks then\n"
            "      announced := true\n"
            "      checked := true\n"
            "      return ()\n"
            "    else\n"
            "      announced := true\n"
            "      return ()"),
        "refinement": (
            "a faithful counterpart guards ONLY the check-routine invocation by the "
            "request flag but leaves the progress announcement OUTSIDE the guard, so "
            "the 'Performing system checks...' banner is emitted even under a skip "
            "request. The FAIL_TO_PASS test asserts that message is ABSENT when the "
            "skip is requested, so it FAILS. It would NOT resolve — the announcement "
            "must be suppressed together with the checks, not printed independently."
        ),
        "rationale": (
            "REJECT from (C1) `announced = (!skipChecks)`: under a skip request the "
            "post-image demands `announced` false, but the rival emits the "
            "announcement unconditionally, leaving `announced` true. (C2) `checked` "
            "is correct here, so this rival isolates the announced clause — the "
            "clause `weak-check-under-skip` leaves correct. Refuted at "
            "skipChecks=true (mut inits false)."
        ),
        "witness": _tester(
            "example : runStartupChecksTester true false false = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-never-perform",
        "kind": "uniqueness",
        "expect": "reject",
        # The other-corner attack: perform NEITHER effect, regardless of the flag.
        # Correct under a skip request, wrong when no skip is requested (both
        # observables stay false where the spec forces true). Attacks BOTH clauses
        # in the skip=false sub-domain, exercising the OTHER value of the free
        # binder (no other reject witness sits at skip=false).
        "module": _impl(
            "    -- Perform neither effect, regardless of the request flag.\n"
            "    return ()"),
        "refinement": (
            "a faithful counterpart that never emits the announcement and never "
            "invokes the check routine — as if the checks were unconditionally "
            "skipped — is wrong when no skip is requested. The FAIL_TO_PASS test "
            "also invokes the command WITHOUT the skip request and asserts the "
            "'Performing system checks...' message IS present and the check routine "
            "IS called; an impl that never performs them FAILS that half of the "
            "test. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from BOTH clauses (C1) and (C2) in the OTHER sub-domain: when no "
            "skip is requested the post-image demands both observables true, but the "
            "rival leaves both false. Refuted at skipChecks=false (mut inits false) — "
            "the value of the free binder that the skip-request rivals do not probe, "
            "so this witness moves `skipChecks` across the whole two-point domain."
        ),
        "witness": _tester(
            "example : runStartupChecksTester false false false = false := by\n"
            "  decide\n"),
    },
    # =====================================================================
    # ADDED BY AUDIT — the two rivals that complete the clause x corner matrix.
    # The shipped rivals attacked (C1) and (C2) in isolation only at
    # skipChecks=true, and covered skipChecks=false only JOINTLY (both clauses
    # violated at once, weak-never-perform). So a spec that had lost ONE clause
    # in the no-skip sub-domain would still have been rejected by every shipped
    # case — the surviving clause refutes weak-never-perform on its own. These
    # two rivals close that: each performs exactly ONE effect when no skip is
    # requested, so exactly one clause is violated at skipChecks=false. Both were
    # built and both are rejected; each witness elaborates against its rival and
    # is refuted by `decide` on the frozen solution.
    # =====================================================================
    {
        "id": "weak-checked-omitted-noskip",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the announcement but never invoke the check routine. (C1) holds on
        # the whole domain; (C2) is violated at skipChecks=false ONLY. Isolates
        # the `checked` clause in the sub-domain no shipped rival isolates.
        "module": _impl(
            "    -- Emit the progress announcement when the checks are not skipped, but\n"
            "    -- never invoke the check routine at all.\n"
            "    if !skipChecks then\n"
            "      announced := true\n"
            "      return ()\n"
            "    else\n"
            "      return ()"),
        "refinement": (
            "a faithful counterpart emits the progress announcement under the "
            "correct condition but never invokes the check routine on any path — "
            "the banner is printed and nothing is actually validated. The "
            "FAIL_TO_PASS test also invokes the command WITHOUT the skip request "
            "and asserts the check routine IS called; a counterpart that never "
            "invokes it FAILS that half of the test. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from (C2) `checked = (!skipChecks)` in the no-skip sub-domain: "
            "when no skip is requested the post-image demands `checked` true, but "
            "the rival leaves it false. (C1) `announced` is correct on BOTH values "
            "of the flag, so this rival isolates C2 at skipChecks=false — the "
            "clause/corner cell that weak-never-perform covers only jointly with "
            "C1. Refuted at skipChecks=false (mut inits false)."
        ),
        "witness": _tester(
            "example : runStartupChecksTester false false false = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-announced-omitted-noskip",
        "kind": "uniqueness",
        "expect": "reject",
        # The DUAL: invoke the check routine but never emit the announcement.
        # (C2) holds on the whole domain; (C1) is violated at skipChecks=false
        # ONLY. Isolates the `announced` clause in that sub-domain.
        "module": _impl(
            "    -- Invoke the check routine when the checks are not skipped, but never\n"
            "    -- emit the progress announcement at all.\n"
            "    if !skipChecks then\n"
            "      checked := true\n"
            "      return ()\n"
            "    else\n"
            "      return ()"),
        "refinement": (
            "a faithful counterpart invokes the check routine under the correct "
            "condition but never emits the progress announcement on any path — the "
            "checks run silently. The FAIL_TO_PASS test invokes the command WITHOUT "
            "the skip request and asserts the 'Performing system checks...' message "
            "IS present; a counterpart that never emits it FAILS that half of the "
            "test. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from (C1) `announced = (!skipChecks)` in the no-skip "
            "sub-domain: when no skip is requested the post-image demands "
            "`announced` true, but the rival leaves it false. (C2) `checked` is "
            "correct on BOTH values of the flag, so this rival isolates C1 at "
            "skipChecks=false, the dual of weak-checked-omitted-noskip. Refuted at "
            "skipChecks=false (mut inits false)."
        ),
        "witness": _tester(
            "example : runStartupChecksTester false false false = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus a 2-case AXIOM lane. The
# sibling contracts TWO functions: `offers_skip_request() -> bool` (the argparse
# exposure of the skip option, pinned to the constant True) and
# `startup_action_schedule(skip_checks) -> List[int]` (a three-code action
# schedule: ANNOUNCE, RUN, and an always-on MIGRATION re-check). This velvet
# bundle models a NARROWER surface — ONE method, `runStartupChecks`, gating just
# the two suppressible effects (the announcement and the check invocation) as two
# boolean occurrence flags — which is why most sibling cases have no counterpart
# (carrier narrowing, not an omission of convenience). Every sibling SPEC case is
# accounted for below.
#
#   nagini case                -> here                          disposition
#   --------------------------------------------------------------------------
#   pos-control-schedule        -> pos-branch-invert            PORTED (branch invert)
#   pos-control-offers          -> (none)                       OMITTED (unmodeled fn)
#   admiss-schedule             -> admiss-both-corners          RE-AIMED
#   weak-skip-not-honored       -> weak-skip-not-honored        PORTED (= prepatch)
#   weak-skip-emits-run         -> weak-check-under-skip        PORTED
#   weak-drop-migration         -> (none)                       OMITTED (unmodeled observable)
#   weak-wrong-order            -> (none)                       VACUOUS (unobservable order)
#   weak-offers-false           -> (none)                       OMITTED (unmodeled fn)
#   (no sibling)                -> pos-direct-assign             ADDED (2nd correct shape)
#   (no sibling)                -> weak-announce-under-skip      ADDED (isolates C1)
#   (no sibling)                -> weak-never-perform            ADDED (skip=false corner)
#   (no sibling)                -> weak-checked-omitted-noskip   ADDED BY AUDIT (C2 @ skip=false)
#   (no sibling)                -> weak-announced-omitted-noskip ADDED BY AUDIT (C1 @ skip=false)
#   AXIOM_TESTS (2)             -> (none)                        DROPPED (G-AX)
#   frame-mutation              -> (none)                        VACUOUS
#
# PORTED (positives): pos-control-schedule inverts the branch; here
#   pos-branch-invert does the same (skip in the `if`, no-skip in the `else`),
#   writing both observables to `!skipChecks` just as gold does, so the frozen
#   `loom_solve` closes the byte-identical obligation (verified out-of-band).
# ADDED (pos-direct-assign): a second structurally-different correct positive —
#   a branch-free `announced := !skipChecks; checked := !skipChecks` — carries the
#   spirit of the sibling's pos-control-offers ("a different-shaped correct impl
#   must verify") on the modeled surface, since offers_skip_request itself is not
#   modeled here (see OMITTED). Verified out-of-band.
# RE-AIMED (admissibility): the sibling self-calls startup_action_schedule on both
#   bool inputs and asserts the pinned postconditions hold. Here the precondition
#   is on the two `mut` observables (`announced = false ∧ checked = false`, the
#   fresh-entry state); admiss-both-corners keeps the gold impl and discharges an
#   in-region assert pinning the post-image formula at BOTH request-flag corners
#   (non-degenerate: skip forces both false, no-skip forces both true), so the
#   require clauses are shown to admit the F2P inputs and the obligation is
#   satisfiable. Verified out-of-band under the frozen `loom_solve`.
# PORTED (rivals): weak-skip-not-honored is the pre-fix bug verbatim (both effects
#   unconditional) attacking both clauses under a skip request. weak-skip-emits-run
#   ports as weak-check-under-skip (gate the announcement, leave the check
#   unconditional -> checked clause C2). Each carries a machine-checked witness that
#   ELABORATES against the rival and FAILS against gold (both builds run out-of-band).
# ADDED (weak-announce-under-skip): this carrier splits the single nagini schedule
#   observable into TWO independent boolean clauses (announced C1, checked C2). The
#   sibling's weak-skip-emits-run attacks the run/check side; its DUAL — gate the
#   check, leave the announcement unconditional -> announced clause C1 — has no
#   sibling because nagini's coupled sequence could not isolate it, and is added so
#   BOTH top-level clauses are independently attacked (not only jointly by
#   weak-skip-not-honored). Genuine SPEC-TOO-WEAK probe with a discriminating witness.
# ADDED (weak-never-perform): perform neither effect regardless of the flag; wrong
#   only when no skip is requested. Refuted at skipChecks=false, the OTHER value of
#   the single free binder — no skip-request rival sits there — so the battery moves
#   `skipChecks` across its entire two-point domain rather than pinning it at true.
# OMITTED (pos-control-offers, weak-offers-false): the sibling's offers_skip_request
#   models the argparse exposure of the --skip option, pinned to the constant True.
#   THIS bundle does not model that function — the option registration is a
#   declarative argparse action with no algorithmic content and is folded into the
#   FREE boolean input `skipChecks` (mapping.md §1, meta.additional_change_sites),
#   so there is no `offers_skip_request` obligation to defend or attack. Omitted as
#   a genuine carrier fact, not an effort gap.
# OMITTED (weak-drop-migration): the sibling's schedule carries an always-on
#   MIGRATION re-check code that its rival folds into the suppressible pass. This
#   bundle models ONLY the two SUPPRESSIBLE effects (announcement, check invocation);
#   the always-on migration re-check is not part of the gated behaviour and is not a
#   modeled observable (no `ensures` clause pins it), so there is no clause for such
#   a rival to violate. Omitted as unmodeled, not because it was hard to prove.
# VACUOUS (weak-wrong-order): the sibling pins the EXACT emission ORDER of the two
#   effects in a `List[int]` sequence, so running validation before announcing it is
#   a distinct schedule. On this carrier the two effects are modeled as set-once
#   BOOLEAN occurrence flags and the spec pins only their FINAL state (`announced`,
#   `checked`), not the order in which they were written; the two orderings produce
#   the same post-state, so no witness can discriminate them. The distinction the
#   sibling kept is collapsed by this abstraction — a rival that reorders is NOT
#   wrong on this carrier. Dropped per the porting map (no discriminating witness
#   exists), not fabricated. DEMONSTRATED by the audit rather than argued: the
#   reordered impl (write `checked` first, then `announced`, inside the same guard)
#   was built against the frozen spec and VERIFIES (exit 0). A rival the spec
#   SATISFIES cannot carry a refutation witness, so the case is vacuous here as a
#   measured fact. It is also not a spec hole: the reordered impl is observably
#   identical on this carrier (same final state at both flag values), and the
#   ordering it permutes is between two writes whose real counterparts are both
#   suppressed or both performed together, so its faithful counterpart still
#   resolves the test.
# VACUOUS (frame-mutation): the sibling already records this class N/A — its only
#   input is a primitive `bool` passed by value, no `Acc(x,1/2)` read-only reference
#   to overwrite. This backend is referentially transparent a fortiori: `skipChecks`
#   is an immutable value and the two `mut` observables are pinned outputs, not
#   aliased heap. No substitute probe is fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
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
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   axioms and no deep-model references (the two effects are modeled directly as
#   occurrence flags), so there is nothing to probe and the gate ignores it.
#
# CLAUSE / BINDER COVERAGE. The battery attacks each of the two independent
#   top-level clauses IN ISOLATION at BOTH values of the single free binder — the
#   full 2-clause x 2-corner matrix, which the pre-audit battery covered only on
#   the skip=true half:
#                          skipChecks=true              skipChecks=false
#     (C1) announced       weak-announce-under-skip     weak-announced-omitted-noskip
#     (C2) checked         weak-check-under-skip        weak-checked-omitted-noskip
#     both jointly         weak-skip-not-honored        weak-never-perform
#   Why the two audit-added cells matter: at skipChecks=false the pre-audit battery
#   had only the JOINT rival (weak-never-perform, both clauses violated at once), so
#   a spec that had lost exactly one clause in the no-skip sub-domain would still
#   have rejected every shipped rival — the surviving clause refutes the joint rival
#   by itself. The two added rivals violate exactly one clause there each, so each
#   clause is now load-bearing in both sub-domains.
#   All six reject witnesses probe the input domain at pts=2 DISTINCT points — the
#   ENTIRE two-point domain of the free binder. Rivals sharing an input fail there
#   for DIFFERENT reasons (both clauses / C2 only / C1 only), so none is a near-miss
#   of another needing a separating point. The two positives and the admissibility
#   case defend both clauses. The two `mut` observables are pinned to `false` on
#   entry by the `require` clauses, so `false` is their only admitted value — not a
#   pinned-binder gap. `skipChecks`, the only free binder, takes both values.
AXIOM_TESTS = []
