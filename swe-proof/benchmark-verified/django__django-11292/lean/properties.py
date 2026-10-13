"""properties.py — G-PBT falsification battery for django__django-11292 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` is changed, so ``markers.same_spec`` holds and the
``theorem correct_runCommand`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff (in scope AND it
does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

DEFENDED SURFACE (one obligation, one total function over Bool × Bool)
----------------------------------------------------------------------

  problem_spec_runCommand
      (commandPerformsChecks skipRequested : Bool) (result : RunResult) : Prop

  Four INDEPENDENT top-level conjuncts, one per point of the input domain, each
  pinning the outcome to a distinct constructor of the three-valued ``RunResult``:

    C1  cPC = false → sR = false → result = skippedChecks
    C2  cPC = false → sR = true  → result = unrecognizedOption
    C3  cPC = true  → sR = true  → result = skippedChecks    <- THE fix's clause
    C4  cPC = true  → sR = false → result = ranChecks

  The two Boolean binders exhaust the domain, so the result is FULLY pinned at
  every input: there is no free component and no under-determined sub-domain.
  ``RunResult`` has THREE inhabitants, not two, so a wrong outcome can miss in
  two directions at the same input — a rival at ``(true, true)`` may answer
  ``ranChecks`` (the checks ran anyway) or ``unrecognizedOption`` (the launch was
  rejected outright), and those are DIFFERENT defects with different real-world
  patches. The battery separates them.

  The load-bearing clause is C3: a command that performs checks, asked to skip
  them, must skip them. That is the entire content of the change this instance
  makes, and it is the clause the failing test exercises.

ADVERSARIAL READ of the nagini classes on this carrier
-----------------------------------------------------

  * PARTIAL-DOMAIN (the sibling's whole reject surface, and ours). The nagini
    file's stated leverage is "a rival correct on 3 of the 4 combinations but
    diverging on ONE — most importantly the discriminating combination the whole
    change exists to fix". That argument ports directly and is the reason every
    rival below exists. Because ``RunResult`` is three-valued, this carrier
    admits MORE partial-domain rivals than the sibling's boolean carrier did, and
    two are added for the outcome the sibling could not express (a launch
    rejected as an unrecognised option).

  * FRAME / PERMISSION MUTATION — VACUOUS, and the sibling says so itself: both
    of its modeled functions take their inputs by value, so it has no read-only
    heap footprint to overwrite and it omits the class with justification. The
    same holds a fortiori here — Lean is referentially transparent, both binders
    are immutable ``Bool`` values, there is no aliasing and no permission system.
    No substitute probe is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, again as the sibling argues: every clause
    equates the result to a CONSTRUCTOR determined by the inputs, so there is no
    opaque answer key a rival could echo without doing the work. The bundle
    declares no ``opaque`` and no ``axiom`` (meta.json ``axioms == []``,
    ``deep_model_references == []``). The honest analogue is the cheapest correct
    reshape, carried as a POSITIVE control.

  * DIVERGENCE / NON-TERMINATION — VACUOUS here, on two independent grounds.
    First, the nagini sibling carries no ``diverge-*``/``nonterm-*``/
    ``weak-diverge`` case, so there is nothing to port. Second, and more
    fundamentally, ``implementation_runCommand`` is a total Lean ``def``: a
    diverging implementation cannot be written at all, so the known
    ``partial``-semantics spec hole (the corpus-wide termination-semantics finding), under which a
    non-terminating impl satisfies every clause vacuously while its faithful real
    patch hangs the failing test, DOES NOT EXIST on this backend. Recorded as
    vacuous rather than as a hole, and no reject case is claimed dropped for it.

  * ADMISSIBILITY — RE-AIMED. The sibling's ``admiss-self-call-fshaped`` asserts
    that an empty precondition admits a normal, F2P-shaped input. Here
    ``correct_runCommand`` carries NO precondition hypothesis at all (the
    ``∀ cPC sR`` is unguarded — the behavior is total over Bool × Bool), so
    "a normal input is admitted" is degenerate: every input is. The residual
    admissibility risk that IS real is that the four conjuncts are jointly
    SATISFIABLE by a gold-shaped computation, and the frozen impl discharging all
    four is exactly that witness. Kept as one case; see ``admiss-gold-total``.

WITNESSES
---------
On a tactic-proof backend "did not verify" is the DEFAULT outcome of reshaping an
implementation — the frozen ``subst h1 <;> subst h2 <;> rfl`` script is tuned to
the frozen ``Id.run do`` form — so a rejection alone attributes NOTHING to the
spec. Measured on all seven rivals here: every one fails with ``Tactic `rfl`
failed``, which is precisely the signal that cannot be trusted. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate NEGATED at concrete inputs.

The carrier is fully transparent (two ``Bool`` binders, a ``DecidableEq``
three-constructor result, no opaque callee), so no witness needs to condition on
the carrier: each states ``¬ problem_spec_runCommand <lit> <lit>
(implementation_runCommand <lit> <lit>)`` and discharges it by ``decide``. No
witness binds a hypothesis, so no witness can be inconsistent and no consistency
probe is required.

Every witness was checked out-of-band with scripts/lean_verify.sh in the
obligation-stripped file the gate builds: each ELABORATES against its rival
(exit 0) and FAILS against the frozen solution (``Tactic `decide` proved that the
proposition ... is false``, because gold satisfies the spec at every input). So
each is a seen discriminator, not a tautology.

BINDER AND CLAUSE COVERAGE
--------------------------
  * Reject witness points: ``(true, true)``, ``(true, false)``, ``(false, true)``,
    ``(false, false)`` — all FOUR points of the domain, i.e. pts=4 on a spec with
    exactly four. Neither binder is held at a single value by the reject
    witnesses: ``commandPerformsChecks`` takes true (ignore-skip-request,
    no-skip-option, inverted-skip-polarity, never-run-checks) and false
    (always-offer-skip-option, ignore-performs-checks); ``skipRequested`` takes
    true (ignore-skip-request, no-skip-option, always-offer-skip-option) and
    false (never-run-checks, ignore-performs-checks). So no rival that mishandled
    only one binder could slip through unnoticed.
  * All four independent clauses are attacked: C1 by ignore-performs-checks and
    reject-plain-launch-of-non-checking, C2 by always-offer-skip-option and
    ignore-performs-checks, C3 by ignore-skip-request / no-skip-option /
    inverted-skip-polarity, C4 by inverted-skip-polarity and never-run-checks.
  * Both directions of a wrong three-valued outcome are attacked at the
    load-bearing clause C3: ignore-skip-request answers ``ranChecks`` there,
    no-skip-option answers ``unrecognizedOption``. They share the input point
    because they really do fail at the same input, but each witness additionally
    PINS its rival's own wrong constructor, so neither case claims a sub-domain
    the manifest does not demonstrate. The same is now true of C1:
    ignore-performs-checks answers ``ranChecks`` at (false, false) and
    reject-plain-launch-of-non-checking answers ``unrecognizedOption`` there
    (added by audit — the ported battery attacked C1 in only one of the two
    available wrong directions).
  * The one obligation is DEFENDED by three ``expect="verify"`` soundness cases
    plus one admissibility case, and ATTACKED by seven ``expect="reject"`` cases.
  * Every rival's truth table was machine-evaluated against gold's at all four
    inputs (``#eval`` on each impl side by side): each differs from gold at the
    points its rationale claims and NOWHERE else, so no case is vacuous by being
    definitionally equal to the frozen impl on this carrier.

AXIOM lane: DROPPED. ``AXIOM_TESTS = []``. The sibling carries axiom-soundness /
containment probes over the real command-line argument parser; that lane belongs
to G-AX (axiom_check.py / mapping.md), the G-PBT gate ignores ``AXIOM_TESTS``
regardless, and this bundle consumes no callee axiom anyway.
"""
from pathlib import Path

INSTANCE = "django__django-11292"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single anchor: the WHOLE frozen implementation definition. It lies
# entirely between `-- impl-start` and `-- impl-end` and is unique in the file
# (both asserted by _swap at load time), so every variant's edit is confined to
# the impl region by construction and `same_spec` holds. The frozen proof body is
# NEVER touched: each positive below computes gold's outcome at every input, so
# the frozen tactic script still closes it (confirmed by real builds), and each
# rival is judged by its witness rather than by whether that script happens to
# break. Note what "the frozen script still closes it" does NOT say: it is a
# statement about these three shapes, not about the spec's tolerance in general.
# Audit measured that separately — five FURTHER correct reshapes (helper `def`s,
# `Bool.casesOn`, `cond`, an equality-driven dispatch, and a
# double-negated monadic scaffold) each verify under the frozen tactic body too,
# so the spec is not over-fitted to the frozen boolean algebra or to `Id.run do`.
# ---------------------------------------------------------------------------
_IMPL = """\
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  -- A skip option is registered for this command exactly when it performs checks.
  let skipOptionAvailable := commandPerformsChecks
  -- A skip request for a command with no such option is not recognised.
  if skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  -- When the option is available, an absent request reads as "do not skip".
  let skip := skipRequested
  if commandPerformsChecks && !skip then
    return RunResult.ranChecks
  return RunResult.skippedChecks"""


def _impl(new_body):
    """Full Solution.lean with ONLY the implementation definition replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _wit(*points):
    """Refutation witness: the spec predicate NEGATED at each concrete point.

    Fully transparent carrier (two `Bool`s, a `DecidableEq` result), so `decide`
    discharges each statement directly; no hypothesis is bound, hence nothing to
    be inconsistent about.
    """
    return "\n".join(
        f"example : ¬ problem_spec_runCommand {p}\n"
        f"    (implementation_runCommand {p}) := by\n"
        "  unfold problem_spec_runCommand implementation_runCommand\n"
        "  decide\n"
        for p in points)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG (the spec would be over-fitted to
    # the frozen code form rather than to the behavior). Each returns a value
    # definitionally equal to gold at every input, so the frozen proof body
    # closes it unchanged and the obligation statement stays byte-identical.
    # Every one was confirmed to verify with a real build.
    # =====================================================================
    {
        "id": "pos-nested-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Re-shaped control flow: dispatch on the request FIRST and nest the
        # command's own checking property inside, instead of testing the
        # unrecognised-option condition up front and then the check gate. Same
        # outcome at all four inputs; no intermediate bindings at all.
        "module": _impl("""\
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  if skipRequested then
    if commandPerformsChecks then
      return RunResult.skippedChecks
    return RunResult.unrecognizedOption
  if commandPerformsChecks then
    return RunResult.ranChecks
  return RunResult.skippedChecks"""),
        "rationale": (
            "a CORRECT impl with a different control shape — outer dispatch on "
            "whether a skip was asked, the command's checking property nested "
            "inside, and both intermediate bindings dropped. It agrees with gold "
            "at all four inputs, so it must satisfy C1-C4; if it could not, the "
            "spec would be pinned to the frozen branch ORDER rather than to the "
            "outcome => SPEC-TOO-STRONG. Ports the sibling's structural-reshape "
            "positive for the check-gate function. Verified with a real build; "
            "the frozen tactic body closes it unchanged."),
    },
    {
        "id": "pos-direct-boolean-no-scaffold",
        "kind": "soundness",
        "expect": "verify",
        # Drop the imperative scaffold entirely: no `Id.run do`, no early
        # returns, no intermediate `let`s — a single if/else-if/else expression
        # over the two inputs. This is the sibling's "collapse the branch into
        # the direct boolean form" positive, re-expressed for a three-valued
        # result.
        "module": _impl("""\
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult :=
  if skipRequested && !commandPerformsChecks then
    RunResult.unrecognizedOption
  else if commandPerformsChecks && !skipRequested then
    RunResult.ranChecks
  else
    RunResult.skippedChecks"""),
        "rationale": (
            "the cheapest CORRECT re-expression: the monadic scaffold and both "
            "intermediate bindings collapse into one conditional expression, and "
            "the availability of a skip option is inlined as the command's own "
            "checking property. Definitionally the same function, so C1-C4 must "
            "still discharge; else SPEC-TOO-STRONG (over-fitted to the `Id.run "
            "do` form). Re-expresses the sibling's direct-boolean positive on "
            "this carrier. Verified with a real build."),
    },
    {
        "id": "pos-explicit-truth-table",
        "kind": "soundness",
        "expect": "verify",
        # Third correct shape: no boolean connectives at all — match jointly on
        # the two inputs and name the outcome of each of the four cases. This is
        # the shape furthest from gold's `&&`/`!` gate while still being the same
        # function, so it is the sharpest test that the spec pins the OUTCOME.
        "module": _impl("""\
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  match commandPerformsChecks, skipRequested with
  | false, false => return RunResult.skippedChecks
  | false, true  => return RunResult.unrecognizedOption
  | true,  true  => return RunResult.skippedChecks
  | true,  false => return RunResult.ranChecks"""),
        "rationale": (
            "a CORRECT per-combination decision that names each of the four "
            "outcomes explicitly and uses no boolean connective whatsoever. It "
            "realises exactly the gold truth table, so it must verify; if it "
            "could not, the spec would be pinned to the particular boolean "
            "ALGEBRA of the frozen gate rather than to the decision => "
            "SPEC-TOO-STRONG. Ports the sibling's per-combination branching "
            "positive. Verified with a real build."),
    },

    # =====================================================================
    # ADMISSIBILITY — re-aimed from the sibling's empty-precondition self-call
    # (see the module docstring): `correct_runCommand` has NO precondition
    # hypothesis, so "a normal input is admitted" is degenerate here. What is
    # still worth checking is that the four conjuncts are JOINTLY SATISFIABLE by
    # a gold-shaped computation over the whole domain — an unsatisfiable
    # postcondition would make every soundness positive fail for a reason having
    # nothing to do with the impl.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        # AUDIT REPAIR. This case used to be `_BASE` verbatim — the frozen file
        # unchanged. It verified honestly, but it re-ran what G-VERIFY already
        # runs and carried NO assertion of its own, so the satisfiability claim
        # its rationale made was argued rather than demonstrated. Now the
        # satisfiability is stated as three checked propositions inside the impl
        # region (so `same_spec` holds and the obligation stays byte-identical):
        # the clause set holds at the discriminating input specifically, it holds
        # at EVERY input of the domain, and the discriminating input's outcome is
        # pinned to a concrete constructor. An unsatisfiable clause set — or one
        # satisfiable only away from the load-bearing point — now fails the case
        # instead of passing it silently.
        "module": _impl(_IMPL + """

-- ADMISSIBILITY, machine-checked rather than asserted.
example : problem_spec_runCommand true true
    (implementation_runCommand true true) := by
  unfold problem_spec_runCommand implementation_runCommand
  decide

example : ∀ (commandPerformsChecks skipRequested : Bool),
    problem_spec_runCommand commandPerformsChecks skipRequested
      (implementation_runCommand commandPerformsChecks skipRequested) := by
  unfold problem_spec_runCommand implementation_runCommand
  decide

example : implementation_runCommand true true = RunResult.skippedChecks := by
  unfold implementation_runCommand
  decide"""),
        "rationale": (
            "the obligation is unguarded (`∀ cPC sR`, no precondition), so the "
            "sibling's 'the empty precondition admits the F2P-shaped input' probe "
            "is degenerate — every input is admitted. Re-aimed at the residual "
            "risk: C1-C4 pin three DIFFERENT outcomes across an exhaustively "
            "covered domain, and if they were jointly unsatisfiable no impl could "
            "ever discharge them. The impl is gold's, and the case now CHECKS the "
            "satisfiability instead of asserting it: `problem_spec_runCommand` is "
            "discharged by `decide` at the discriminating input, then over the "
            "whole Bool × Bool domain, and the discriminating input's outcome is "
            "pinned to `skippedChecks`. Must verify, else SPEC-UNSATISFIABLE — "
            "and a clause set satisfiable only AWAY from the load-bearing point "
            "now fails here rather than passing."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries the refinement argument for why its
    # faithful real counterpart would NOT resolve the failing test, plus a
    # refutation witness checked (two real builds) to hold of the rival and to
    # FAIL on gold. All seven were confirmed to be rejected by a real build — and
    # all seven failed with `Tactic `rfl` failed`, which is exactly why the witness
    # rather than the rejection is the evidence here.
    # =====================================================================
    {
        "id": "rival-ignore-skip-request",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central attack, and the sibling's central one: the pre-change gate
        # that DISREGARDS the request and checks whenever the command checks.
        # Correct at 3 of 4 inputs; wrong exactly at the discriminating one.
        "module": _impl("""\
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  let skipOptionAvailable := commandPerformsChecks
  if skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  if commandPerformsChecks then
    return RunResult.ranChecks
  return RunResult.skippedChecks"""),
        "refinement": (
            "the request is recognised as a valid option but then ignored by the "
            "decision: a command that performs checks runs them even when the "
            "launch asked to skip. Its faithful real counterpart therefore still "
            "runs the check battery for such a command, so the failing test — a "
            "checking command launched with a deliberately broken project "
            "configuration AND the skip request, expecting a clean run — STILL "
            "reports the configuration error and the test does NOT pass. This is "
            "the exact defect the change corrects, so a rival that verified here "
            "would be a true verify-does-not-imply-resolve break."),
        "rationale": (
            "REJECT from C3 (`cPC = true → sR = true → result = skippedChecks`): "
            "at (true, true) the spec demands skippedChecks and this rival "
            "answers ranChecks. The witness refutes the spec at that point and "
            "additionally PINS the rival's outcome there to ranChecks, which is "
            "what distinguishes it from rival-no-skip-option (same input, the "
            "other wrong constructor). Binders: cPC=true, sR=true. If it "
            "verified => SPEC-TOO-WEAK (the spec admits the original defect)."),
        "witness": (
            "example : ¬ problem_spec_runCommand true true\n"
            "    (implementation_runCommand true true) := by\n"
            "  unfold problem_spec_runCommand implementation_runCommand\n"
            "  decide\n\n"
            "example : implementation_runCommand true true = RunResult.ranChecks := by\n"
            "  unfold implementation_runCommand\n"
            "  decide\n"),
    },
    {
        "id": "rival-no-skip-option",
        "kind": "uniqueness",
        "expect": "reject",
        # The other half of the pre-change behavior, and the outcome the
        # sibling's boolean carrier could not express: NO command ever offers a
        # skip option, so any request is an unrecognised option and the launch is
        # rejected. This is the bundle's own prepatch behavior. Wrong at
        # (true, true) — but toward a DIFFERENT constructor than the rival above.
        "module": _impl("""\
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  let skipOptionAvailable := false
  if skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  let skip := skipRequested
  if commandPerformsChecks && !skip then
    return RunResult.ranChecks
  return RunResult.skippedChecks"""),
        "refinement": (
            "no command offers the skip option at all, so a launch that asks to "
            "skip is rejected outright as an unrecognised option. Its faithful "
            "real counterpart makes the failing test's invocation fail at "
            "argument-parsing time rather than run cleanly, so that test does NOT "
            "pass — it is the literal pre-change state of this behavior (the "
            "bundle's prepatch variant). A rival that verified here would mean "
            "the spec cannot see the original defect at all."),
        "rationale": (
            "REJECT from C3, in the opposite direction to "
            "rival-ignore-skip-request: at (true, true) the spec demands "
            "skippedChecks and this rival answers unrecognizedOption. The two "
            "rivals share the input point because they genuinely fail at the same "
            "input, so the witness additionally PINS this rival's outcome there "
            "to unrecognizedOption — the three-valued result means these are "
            "distinct defects with distinct real counterparts, and neither case "
            "claims a sub-domain the manifest does not show. Binders: cPC=true, "
            "sR=true. If it verified => SPEC-TOO-WEAK."),
        "witness": (
            "example : ¬ problem_spec_runCommand true true\n"
            "    (implementation_runCommand true true) := by\n"
            "  unfold problem_spec_runCommand implementation_runCommand\n"
            "  decide\n\n"
            "example : implementation_runCommand true true "
            "= RunResult.unrecognizedOption := by\n"
            "  unfold implementation_runCommand\n"
            "  decide\n"),
    },
    {
        "id": "rival-inverted-skip-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        # Inverted-polarity gate: a checking command runs its checks precisely
        # when the launch asked to SKIP them — the exact opposite of the desired
        # behavior on both checking-command inputs. Ports the sibling's
        # inverted-polarity rival.
        "module": _impl("""\
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  let skipOptionAvailable := commandPerformsChecks
  if skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  let skip := skipRequested
  if commandPerformsChecks && skip then
    return RunResult.ranChecks
  return RunResult.skippedChecks"""),
        "refinement": (
            "reads the request with inverted polarity: a checking command runs "
            "its checks only when the launch asked to skip them. A faithful real "
            "counterpart would (a) run the check battery exactly when the user "
            "asked not to, so the failing test still reports the broken "
            "configuration and does NOT pass, and (b) silently stop checking on "
            "an ordinary launch, so commands that must validate before running "
            "no longer do — breaking the already-passing tests that rely on "
            "checks running by default. NOT resolved, on both counts."),
        "rationale": (
            "REJECT from BOTH C3 and C4, the two clauses over a checking "
            "command: at (true, true) the spec demands skippedChecks and the "
            "rival answers ranChecks; at (true, false) the spec demands ranChecks "
            "and the rival answers skippedChecks. The witness refutes the spec at "
            "BOTH points, so the two-clause claim this rationale makes is "
            "demonstrated rather than asserted — and the (true, false) point is "
            "what separates it from rival-ignore-skip-request, which is CORRECT "
            "there. Binders: cPC=true with sR taking both values. If it verified "
            "=> SPEC-TOO-WEAK."),
        "witness": _wit("true true", "true false"),
    },
    {
        "id": "rival-never-run-checks",
        "kind": "uniqueness",
        "expect": "reject",
        # Never run the checks for any command, while still rejecting a request
        # aimed at a command that offers no such option. Correct at 3 of 4
        # inputs; wrong exactly at the ordinary launch of a checking command.
        # Ports the sibling's "skips validation even when no skip was requested"
        # rival.
        "module": _impl("""\
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  let skipOptionAvailable := commandPerformsChecks
  if skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  return RunResult.skippedChecks"""),
        "refinement": (
            "no command ever runs its checks, whether or not a skip was asked. A "
            "faithful real counterpart honours the skip request but ALSO drops "
            "the check battery from every ordinary launch, so a command that must "
            "validate before running proceeds against a broken configuration with "
            "nobody having asked for that — breaking the already-passing "
            "expectation that such commands check by default and admitting "
            "silently invalid configurations. NOT resolved: it trades the "
            "original defect for a worse one."),
        "rationale": (
            "REJECT from C4 (`cPC = true → sR = false → result = ranChecks`): at "
            "(true, false) the spec demands ranChecks and this rival answers "
            "skippedChecks. It shares that point with "
            "rival-inverted-skip-polarity but is a NEAR-MISS by comparison — it "
            "is correct at (true, true), where the polarity rival is also wrong — "
            "so the two are not interchangeable and this one is refuted at the "
            "single point where it actually fails. Binders: cPC=true, sR=false. "
            "If it verified => SPEC-TOO-WEAK."),
        "witness": _wit("true false"),
    },
    {
        "id": "rival-always-offer-skip-option",
        "kind": "uniqueness",
        "expect": "reject",
        # Offer the skip option for EVERY command, including one that performs no
        # checks. Correct at 3 of 4 inputs; wrong exactly where a request aimed
        # at a non-checking command should be rejected as unrecognised. Ports the
        # sibling's "offer the option unconditionally" rival.
        "module": _impl("""\
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  let skipOptionAvailable := true
  if skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  let skip := skipRequested
  if commandPerformsChecks && !skip then
    return RunResult.ranChecks
  return RunResult.skippedChecks"""),
        "refinement": (
            "offers the skip option for every command, including commands that "
            "perform no checks and therefore have nothing to skip. A faithful "
            "real counterpart accepts the request on those commands where the "
            "desired behavior rejects it, so their set of recognised "
            "command-line arguments — and the usage text listing it — changes, "
            "breaking the already-passing tests that enumerate exactly which "
            "options a command accepts. The desired behavior deliberately "
            "conditions the offer on whether the command checks at all, so this "
            "faithful patch does NOT resolve cleanly."),
        "rationale": (
            "REJECT from C2 (`cPC = false → sR = true → result = "
            "unrecognizedOption`): at (false, true) the spec demands the request "
            "be rejected as an unrecognised option and this rival answers "
            "skippedChecks (it silently accepts a request that has no meaning for "
            "the command). It is the case that moves cPC to false while sR stays "
            "true — so the spec's dependence on cPC alone is exercised — and it is "
            "the TIGHTEST rival at (false, true): correct at the other three "
            "inputs, where rival-ignore-performs-checks (which also witnesses "
            "there) is additionally wrong at (false, false). If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _wit("false true"),
    },
    {
        "id": "rival-ignore-performs-checks",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (no sibling counterpart: nagini's gate rivals all held the
        # checking property TRUE, so a rival that mishandles ONLY the
        # non-checking command was never built there). Disregard the command's
        # own checking property entirely and key both the option offer and the
        # decision on the request alone. Wrong at BOTH non-checking inputs.
        "module": _impl("""\
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  let skipOptionAvailable := true
  if skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  let skip := skipRequested
  if !skip then
    return RunResult.ranChecks
  return RunResult.skippedChecks"""),
        "refinement": (
            "disregards whether the command performs checks at all and decides "
            "purely on the request. A faithful real counterpart would run the "
            "check battery on EVERY ordinary launch, including commands that are "
            "defined never to check — invoking validation where it must not run "
            "(and where it may be unsafe or simply fail), which breaks the "
            "already-passing tests for those commands; and it would additionally "
            "accept the skip request on them, where the desired behavior rejects "
            "it. NOT resolved."),
        "rationale": (
            "REJECT from BOTH C1 and C2, the two clauses over a non-checking "
            "command: at (false, false) the spec demands skippedChecks (such a "
            "command simply proceeds) and the rival answers ranChecks; at "
            "(false, true) the spec demands unrecognizedOption and the rival "
            "answers skippedChecks. The witness refutes the spec at BOTH points, "
            "demonstrating the two-clause claim. It is what stops cPC from being "
            "held at true — the failure mode measured on other cells, where a "
            "rival mishandling only the untested binder value would have "
            "verified; rival-reject-plain-launch-of-non-checking (added by audit) "
            "reaches (false, false) too, but in the other wrong direction "
            "(unrecognizedOption where this one answers ranChecks). No sibling "
            "counterpart: nagini's gate rivals all held the checking property "
            "true. If it verified => SPEC-TOO-WEAK."),
        "witness": _wit("false false", "false true"),
    },
    {
        "id": "rival-reject-plain-launch-of-non-checking",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (no sibling counterpart, and no counterpart in the
        # ported battery either). Gap it closes: across all six ported rivals,
        # `unrecognizedOption` was only ever produced where the spec ALSO wants
        # it (false, true), or at (true, true) by rival-no-skip-option. NO case
        # made a rival answer `unrecognizedOption` where the spec wants a command
        # to simply proceed. So the clause "a command that performs no checks and
        # was not asked to skip proceeds" (C1) was attacked in exactly ONE
        # direction (ranChecks, by rival-ignore-performs-checks) out of the two a
        # three-valued result allows. This rival rejects the ORDINARY launch of a
        # non-checking command as an unrecognised option, and is correct at the
        # other three inputs — a single-point near-miss, machine-checked against
        # gold's truth table at all four points.
        "module": _impl("""\
def implementation_runCommand
    (commandPerformsChecks skipRequested : Bool) : RunResult := Id.run do
  let skipOptionAvailable := commandPerformsChecks
  if !skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  if skipRequested && !skipOptionAvailable then
    return RunResult.unrecognizedOption
  let skip := skipRequested
  if commandPerformsChecks && !skip then
    return RunResult.ranChecks
  return RunResult.skippedChecks"""),
        "refinement": (
            "treats the ABSENCE of a skip request as the unrecognised thing for a "
            "command that performs no checks: such a command can no longer be "
            "launched in the ordinary way at all, its launch is rejected before "
            "it runs. A faithful real counterpart makes every plain invocation of "
            "a non-checking command fail at argument-parsing time instead of "
            "doing its work, so the already-passing expectations that such a "
            "command runs and produces its output break, while the discriminating "
            "launch this change exists to enable is unaffected. NOT resolved: it "
            "leaves the target behavior correct and breaks a neighbouring one."),
        "rationale": (
            "REJECT from C1 (`cPC = false → sR = false → result = "
            "skippedChecks`): at (false, false) the spec demands the command "
            "simply proceed and this rival answers unrecognizedOption. It shares "
            "that point with rival-ignore-performs-checks but misses in the OTHER "
            "of the two available wrong directions (that rival answers ranChecks "
            "there), so C1 is now attacked toward both non-conforming "
            "constructors, as C3 already was. It is also the tighter near-miss of "
            "the two: correct at (false, true), where "
            "rival-ignore-performs-checks is also wrong. The witness refutes the "
            "spec at (false, false) and PINS this rival's outcome there to "
            "unrecognizedOption. Binders: cPC=false, sR=false. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": (
            "example : ¬ problem_spec_runCommand false false\n"
            "    (implementation_runCommand false false) := by\n"
            "  unfold problem_spec_runCommand implementation_runCommand\n"
            "  decide\n\n"
            "example : implementation_runCommand false false "
            "= RunResult.unrecognizedOption := by\n"
            "  unfold implementation_runCommand\n"
            "  decide\n"),
    },
]


# ===========================================================================
# NAGINI -> LEAN ACCOUNTING (every sibling case is dispositioned).
#
#   nagini case                         -> here
#   -----------------------------------------------------------------------
#   pos-pos-bool-collapse               -> pos-direct-boolean-no-scaffold
#                                                                  RE-EXPRESSED
#   pos-wrv-direct-boolean              -> pos-nested-branch-reorder RE-SHAPED
#   pos-wrv-demorgan-nested             -> pos-explicit-truth-table  PORTED
#   admiss-self-call-fshaped            -> admiss-gold-total         RE-AIMED
#   weak-wrv-drop-skip-discriminating   -> rival-ignore-skip-request PORTED
#   weak-wrv-inverted-skip-polarity     -> rival-inverted-skip-polarity PORTED
#   weak-wrv-flip-no-skip-combo         -> rival-never-run-checks    PORTED
#   weak-pos-constant-true              -> rival-always-offer-skip-option PORTED
#   weak-pos-constant-false             -> rival-no-skip-option      PORTED
#   (no sibling)                        -> rival-ignore-performs-checks
#                                                       ADDED (cPC=false binder)
#   (no sibling)                        -> rival-reject-plain-launch-of-non-checking
#                                              ADDED BY AUDIT (C1, other direction)
#   AXIOM_TESTS (2)                     -> (none)                   DROPPED
#
# NOTHING WAS OMITTED FOR DIFFICULTY. Every sibling SPEC case has a counterpart
# above; the only sibling content dropped is its 2-case AXIOM lane, which the
# G-PBT gate ignores by contract and which belongs to G-AX. No soundness positive
# was dropped for an unclosable proof: all three positives close under the frozen
# tactic body, confirmed by real builds, and none required reproving, a helper
# lemma, or any weakening of the obligation.
#
# CARRIER NARROWING AND WIDENING. The sibling contracts TWO boolean functions —
# whether the skip option is offered, and whether the checks then run — and gets
# a 2 x 4 boolean surface. This bundle folds both into ONE obligation whose
# result is a THREE-valued outcome, which is a narrowing in case count (one
# `theorem correct_*` versus two contracts, so the two sibling function surfaces
# collapse into four clauses of one predicate) and a WIDENING in expressiveness:
# the launch being rejected outright as an unrecognised option is a distinct
# observable here, where the sibling could only encode "the option was not
# offered" as a boolean. That is why the option-offer rivals port to
# rival-no-skip-option / rival-always-offer-skip-option, and why the two
# same-input rivals at (true, true) are genuinely different defects rather than
# duplicates.
#
# CLASSES RECORDED AS VACUOUS (not fabricated, not silently skipped):
#   FRAME / PERMISSION MUTATION — vacuous, and the sibling omits it too: both its
#     functions take their inputs by value. Here both binders are immutable
#     `Bool` values on a referentially-transparent carrier; there is no read-only
#     footprint to overwrite. Nor is there a frame CLAUSE to attack in its place:
#     the result is a single scalar outcome, fully pinned at every input, with no
#     preserved-input component a rival could quietly rewrite.
#   UNGROUNDED-ORACLE ECHO — vacuous. Every clause equates the result to a
#     constructor determined by the inputs; meta.json `axioms == []` and
#     `deep_model_references == []`, so there is no opaque answer key to echo.
#   DIVERGENCE / NON-TERMINATION — vacuous on this backend, NOT a spec hole. The
#     sibling carries no diverge-*/nonterm-*/weak-diverge case, and
#     `implementation_runCommand` is a total Lean `def`, so a non-terminating
#     rival cannot be written at all; the `partial`-semantics hole documented in
#     the corpus-wide termination-semantics finding — where a diverging impl satisfies every clause
#     vacuously while its faithful patch hangs the failing test — does not arise
#     here. No reject case is claimed dropped for it.
#
# WITNESS MECHANICS: the carrier is fully transparent (two `Bool`s, a
#   `DecidableEq` three-constructor result, no opaque callee), so every witness
#   states the NEGATED spec predicate at concrete literals and closes by
#   `decide`. No witness binds a hypothesis, so none can be inconsistent and no
#   consistency probe is needed. All checked with scripts/lean_verify.sh against
#   the obligation-stripped file: rival build exit 0, gold build exit 1 with
#   `Tactic `decide` proved that the proposition ... is false`.
#
# ===========================================================================
# INDEPENDENT AUDIT RECORD (what a re-run gate cannot recover)
#
# Every claim below was re-derived from real builds, not from the port's notes.
#
# STATEMENT INTEGRITY. Each case's `theorem correct_runCommand` statement was
#   compared to the frozen file's BYTE-FOR-BYTE (raw slice up to `:= by`, not
#   just the whitespace-normalized form `variant_scope` compares): identical in
#   all cases. No case reformats or weakens a hypothesis.
#
# WITNESS DISCRIMINATION, RE-DERIVED. All seven reject witnesses were rebuilt
#   from scratch in the obligation-stripped file the gate constructs: rival exit
#   0, gold exit 1, in every case. Every gold-side failure was read, not just
#   counted, and every one is `Tactic `decide` proved that the proposition ... is
#   false` — a SEMANTIC refutation of the concrete claim. None is an unknown
#   identifier, a type error, an unfolding failure, a timeout, or a stuck
#   reduction (`_STUCK_REDUCTION` does not fire: this carrier has no opaque term
#   and no `Classical.choice`). No witness binds a hypothesis, so
#   `consistency_probe` returns None for all seven — nothing to be inconsistent.
#
# RIVAL vs RESHAPE (are the rivals actually WRONG?). Machine-settled rather than
#   argued: every rival impl and gold were `#eval`-ed side by side at all four
#   inputs. Each rival differs from gold exactly at the points its rationale
#   claims and nowhere else. No rival is definitionally equal to gold, so no case
#   is vacuous — the trap this carrier could have hidden (three-constructor
#   collapsing) does not occur.
#
# SPEC-TOO-WEAK PROBE (attack D). Seven NEW wrong impls the battery did not
#   contain were built against the frozen spec, aimed at the least-probed
#   directions: `unrecognizedOption` where the spec wants a plain launch, both
#   constants, a transposed non-checking pair, a globally swapped
#   ranChecks/skippedChecks, and an offer keyed on the request. Each was tried
#   TWICE — once under the frozen tactic body and once under a strictly stronger
#   best-effort script (`first | rfl | decide | simp [...] | (unfold ...; decide)`),
#   so a rejection cannot be blamed on the frozen script's shape. All 14 builds
#   failed (`unsolved goals` under the strong script). NO spec hole found.
#
# SPEC-TOO-STRONG PROBE (attack E). Five NEW correct reshapes were built:
#   impl-region helper `def`s (`skipOptionOffered` + a 4-case `runOutcome`),
#   nested `Bool.casesOn`, nested `cond` with a negated guard, an
#   equality-driven dispatch (`cPC == sR`), and a double-negated `Id.run do`
#   scaffold. All 10 builds VERIFY — including under the frozen tactic body
#   unchanged. The spec pins the OUTCOME, not the frozen boolean algebra, the
#   branch order, or the monadic scaffold. No soundness hole.
#
# REPAIRS MADE BY THE AUDIT (two defects, both in the battery, none in the spec):
#   1. `admiss-gold-total` was the frozen file VERBATIM (`module: _BASE`). It
#      passed honestly but asserted nothing of its own — it re-ran G-VERIFY's
#      check — while its rationale claimed the four clauses are jointly
#      satisfiable AT the discriminating input. Now the case CHECKS that: three
#      `decide`d propositions in the impl region (the clause set at (true, true),
#      the clause set over the whole domain, and the pinned outcome there).
#   2. C1 was attacked in only ONE of the two wrong directions a three-valued
#      result allows — no rival anywhere in the battery answered
#      `unrecognizedOption` at a point where the spec wants a command to proceed.
#      `rival-reject-plain-launch-of-non-checking` closes that, and is the
#      tightest near-miss at (false, false): correct at the other three inputs.
#   Two prose over-claims were also corrected: `rival-always-offer-skip-option`
#   said it was "the ONLY witness at (false, true)" (rival-ignore-performs-checks
#   witnesses there too) and `rival-ignore-performs-checks` said it was "the ONLY
#   reject case reaching (false, false)" (true when written, no longer). Both now
#   state the sharper, TRUE fact: which of the co-located rivals is the tighter
#   near-miss, and which wrong direction each takes.
#
# OMISSIONS. Nothing is recorded here as inexpressible. Every sibling SPEC case
#   has a counterpart above (see the accounting table); the dropped AXIOM lane is
#   ignored by this gate by contract; and the three vacuous CLASSES above are
#   vacuous for demonstrated carrier reasons (no heap/permissions, no opaque
#   oracle, no `partial` — a total Lean `def` cannot diverge), not for difficulty.
# ===========================================================================
AXIOM_TESTS = []
