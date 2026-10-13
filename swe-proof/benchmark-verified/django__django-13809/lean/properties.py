# properties.py — G-PBT falsification battery for django__django-13809 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for the soundness positive, the proof body — may differ),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   serverStartup : Bool → List StartupAction
#   Models the development server's startup routine as the ordered list of
#   observable steps it emits. A single boolean control (`skipChecks`) gates one
#   two-step prefix (announce-then-run the checks); the prefix is emitted iff the
#   control is false, and is always followed by a fixed tail of steps emitted in a
#   set order regardless of the control. The single postcondition pins the result to
#   the exact ordered concatenation:
#       (if skipChecks then [] else [announce, run]) ++ [checkMigrations, banner, serve]
#   grounded entirely in the one boolean input.
#
# CARRIER NOTE (what this port models, and what it does not): the nagini sibling
# contracted TWO functions — the routine's action schedule AND a separate constant
# predicate reporting that the skip control is OFFERED at all (the argument-
# registration surface). The lean bundle models ONLY the purely-functional core,
# the startup routine, so the "offer the control" predicate has NO counterpart here;
# its nagini cases (a constant-True positive and a constant-False rival) are dropped
# as unmodeled behavior (see 'assessment' in the payload). Conversely, this carrier
# models the FULL tail (migration re-check, banner, serve) as transparent list
# elements, where nagini's schedule modeled only the first tail step — so the tail's
# presence and order become directly attackable clauses here, which nagini could not
# reach. This port therefore attacks both the gated prefix AND the fixed tail.
#
# WHICH RIVALS ARE ALSO TEST-OBSERVABLE (recorded by the audit; read this before
# citing any `refinement` below as a verify-does-not-resolve argument). The
# acceptance test observes exactly four facts: under a skip request the announcement
# is absent from captured output and the check step did not run; with no skip request
# the announcement is present and the check step did run. It substitutes stand-ins for
# the tail steps and asserts nothing about them, and it asserts no relative ORDER
# anywhere. Consequently:
#   * the gated-prefix PRESENCE rivals (weak-skip-not-honored, weak-skip-emits-run,
#     and the audit-added weak-always-skip, weak-gate-inverted) diverge on behaviour
#     the recorded tests DO observe -- these are the genuine verify-does-not-resolve
#     rivals;
#   * the ORDER and fixed-TAIL rivals (weak-wrong-order, weak-drop-migration,
#     weak-drop-serve, weak-tail-reorder) diverge from the SPECIFIED behaviour -- the
#     spec pins the tail and the emission order in both branches, per the frame
#     directive that unchanged outputs be pinned explicitly -- but no recorded test
#     distinguishes them. They remain sound uniqueness attacks on real spec clauses
#     and are kept for that purpose; their `refinement` fields now state this scope
#     instead of overclaiming that they fail the acceptance test.
# The split is a property of the recorded test sets, not of the spec, which is why a
# rejection here is attributed to a spec clause by the witness rather than to a test.
#
# LANES THAT DO NOT PORT:
#   * FRAME / PERMISSION-MUTATION (nagini's fractional-permission class). Lean is
#     referentially transparent — no aliasing, no read-only reference parameter to
#     overwrite — so this class is VACUOUS here. There is no half-permission input;
#     the sole input is a `Bool` by value. See 'assessment'.
#   * ADMISSIBILITY — this lane DOES port, and the second audit landed it as
#     `admiss-f2p-skip-requested`. An earlier pass had recorded it N/A on the
#     grounds that the frozen obligation carries no precondition hypothesis
#     (`∀ (skipChecks : Bool), problem_spec … (implementation …)` has no
#     implication arrow, so nothing can literally be PRECOND-TOO-STRONG). That
#     reason is rejected: on a TOTAL carrier the analogue of a too-strong
#     precondition is the obligation being UNSATISFIABLE at exactly an
#     F2P-shaped input, and a positive that discharges the obligation at that
#     concrete input BY EVALUATION — as a `have`, before closing the frozen
#     obligation verbatim — tests that directly. Measured, not argued: the case
#     verifies (exit 0) and its ground `have`s are load-bearing, failing against
#     four of this battery's own rivals (see the case comment).
#   * AXIOM_TESTS. The spec consumes no opaque/axiom callee (the routine's behavior
#     is modeled DEEPLY as a gated list construction); the axiom lane is G-AX's job
#     and this gate ignores it regardless.
from pathlib import Path

INSTANCE = "django__django-13809"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# impl-region anchors. Each substring below lies ENTIRELY inside the
# impl-start/impl-end region and is unique in the frozen file.
# ---------------------------------------------------------------------------

# The gated two-step prefix, verbatim (guard + the two appends):
_PREFIX = (
    "  if !skipChecks then\n"
    "    log := log ++ [StartupAction.announceChecks]\n"
    "    log := log ++ [StartupAction.runChecks]"
)
assert _BASE.count(_PREFIX) == 1, "prefix impl anchor drifted"

# The mutable-init + guard block (prefix preceded by the empty init), for the
# structural positive control:
_INIT_AND_PREFIX = (
    "  let mut log : List StartupAction := []\n"
    "  if !skipChecks then\n"
    "    log := log ++ [StartupAction.announceChecks]\n"
    "    log := log ++ [StartupAction.runChecks]"
)
assert _BASE.count(_INIT_AND_PREFIX) == 1, "init+prefix anchor drifted"

# The prefix followed by the first tail step (for the fold-migration-into-guard
# rival):
_PREFIX_AND_MIG = (
    "  if !skipChecks then\n"
    "    log := log ++ [StartupAction.announceChecks]\n"
    "    log := log ++ [StartupAction.runChecks]\n"
    "  log := log ++ [StartupAction.checkMigrations]"
)
assert _BASE.count(_PREFIX_AND_MIG) == 1, "prefix+migration anchor drifted"

# The final tail step + return (for the drop-serve rival):
_SERVE_AND_RET = (
    "  log := log ++ [StartupAction.serve]\n"
    "  return log"
)
assert _BASE.count(_SERVE_AND_RET) == 1, "serve+return anchor drifted"

# The last two tail steps in order (for the tail-reorder rival):
_BANNER_SERVE = (
    "  log := log ++ [StartupAction.writeBanner]\n"
    "  log := log ++ [StartupAction.serve]"
)
assert _BASE.count(_BANNER_SERVE) == 1, "banner+serve anchor drifted"

# The gated prefix INCLUDING its trailing newline, so it can be excised whole
# (for the never-emit-the-prefix rival added by the audit):
_PREFIX_NL = _PREFIX + "\n"
assert _BASE.count(_PREFIX_NL) == 1, "prefix+newline anchor drifted"

# The frozen proof's `intro` line (inside the proof-start/proof-end region), so the
# admissibility positive can PREPEND ground `have`s without touching the theorem
# STATEMENT or the spec view. Both stay byte-identical; only the tactic body grows.
_P_INTRO = "  intro skipChecks\n"
assert _BASE.count(_P_INTRO) == 1, "proof intro anchor drifted"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-prefix-as-value: structurally DIFFERENT but behaviourally identical. The frozen
# impl builds the gated prefix with an `if` STATEMENT that conditionally appends the
# two steps to an empty accumulator; this control initialises the accumulator
# directly from a conditional VALUE (the whole prefix chosen as `[]` or the two-step
# list), which is the shape a faithful patch could equally take. The result is
# identical on both inputs, and the frozen `cases skipChecks <;> rfl` proof still
# closes (each branch reduces to a concrete list). If it FAILS => SPEC-TOO-STRONG.
_POS_PREFIX_VALUE = (
    "  let mut log : List StartupAction :=\n"
    "    if skipChecks then [] else [StartupAction.announceChecks, StartupAction.runChecks]"
)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly, edits only the impl region, and carries a witness.
# ---------------------------------------------------------------------------

# weak-skip-not-honored (= the PRE-CHANGE routine): emit the announce+run prefix
# UNCONDITIONALLY — the skip control never gates it.
_WEAK_NOTHONORED = (
    "  log := log ++ [StartupAction.announceChecks]\n"
    "  log := log ++ [StartupAction.runChecks]"
)

# weak-skip-emits-run: gate ONLY the announcement; the check run is emitted even
# under a skip request (the gate was placed around the banner-write alone).
_WEAK_RUNUNDERSKIP = (
    "  if !skipChecks then\n"
    "    log := log ++ [StartupAction.announceChecks]\n"
    "  log := log ++ [StartupAction.runChecks]"
)

# weak-wrong-order: in the no-skip branch, run the checks BEFORE announcing them.
_WEAK_WRONGORDER = (
    "  if !skipChecks then\n"
    "    log := log ++ [StartupAction.runChecks]\n"
    "    log := log ++ [StartupAction.announceChecks]"
)

# weak-drop-migration: fold the always-on migration re-check INSIDE the gated prefix,
# so it is dropped under a skip request.
_WEAK_DROPMIG = (
    "  if !skipChecks then\n"
    "    log := log ++ [StartupAction.announceChecks]\n"
    "    log := log ++ [StartupAction.runChecks]\n"
    "    log := log ++ [StartupAction.checkMigrations]"
)

# weak-drop-serve: drop the final always-on tail step entirely.
_WEAK_DROPSERVE = "  return log"

# weak-tail-reorder: emit the last two always-on tail steps in the wrong order.
_WEAK_TAILREORDER = (
    "  log := log ++ [StartupAction.serve]\n"
    "  log := log ++ [StartupAction.writeBanner]"
)

# weak-always-skip: never emit the gated prefix at all — the control is ignored in
# the OTHER direction from weak-skip-not-honored (which ignored it by always
# emitting). Added by audit: the two existing prefix-presence rivals both over-emit
# under a skip request, so the "prefix MUST be present when the control is off"
# half of the gated-prefix clause was unattacked. This rival is also observably
# wrong on the behaviour the acceptance test pins in BOTH of its two states.
_WEAK_ALWAYSSKIP = ""

# weak-gate-inverted: emit the gated prefix exactly when a skip IS requested —
# the guard's polarity is reversed. Added by audit: wrong at BOTH inputs, so it
# attacks the gate's DIRECTION rather than merely its placement, and it is the
# single rival most directly opposed to the modeled control's meaning.
_WEAK_GATEINVERTED = (
    "  if skipChecks then\n"
    "    log := log ++ [StartupAction.announceChecks]\n"
    "    log := log ++ [StartupAction.runChecks]"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (added by the second audit) — the obligation must be SATISFIABLE
# at the F2P-shaped input, not merely in the abstract.
#
# The frozen theorem is unguarded (`∀ (skipChecks : Bool), …`), so there is no
# precondition hypothesis for a nagini-style call-site probe to attack. The
# analogue on this total carrier is the obligation being unsatisfiable at exactly
# the input the acceptance scenario exercises — a skip REQUESTED — which these two
# ground `have`s discharge by EVALUATION before the frozen obligation is closed
# verbatim underneath them:
#   * `_f2p_admits` discharges the spec predicate itself at `skipChecks = true`;
#   * `_f2p_value` pins WHICH schedule that input produces, so the admission
#     cannot be read off without ever computing the gated branch. (Needed because
#     the spec pins `result` to a term over the same input, so the first `have`
#     alone would read the same if the input landed in any branch at all.)
#
# Both `have`s are load-bearing rather than decorative, MEASURED with the real
# verifier: the identical proof prefix placed against this battery's own rivals
# FAILS — `weak-skip-not-honored`, `weak-gate-inverted` and `weak-drop-serve` each
# fail inside `_f2p_admits` itself (``decide` proved that the proposition … is
# false`), and `weak-always-skip` fails at the frozen `rfl` below. So the case is a
# genuine discharge of the obligation at the F2P-shaped input, not a tautology any
# impl would satisfy. Nothing new is declared (no lemma, axiom or assumption
# token); the theorem STATEMENT and the whole spec view stay byte-identical.
_ADMISS_HAVES = (
    "  have _f2p_admits : problem_spec_serverStartup true\n"
    "      (implementation_serverStartup true) := by\n"
    "    unfold problem_spec_serverStartup implementation_serverStartup tailSteps\n"
    "    decide\n"
    "  have _f2p_value : implementation_serverStartup true =\n"
    "      [StartupAction.checkMigrations, StartupAction.writeBanner,\n"
    "       StartupAction.serve] := by\n"
    "    unfold implementation_serverStartup\n"
    "    decide\n"
)


def _wit(skip):
    """A refutation witness: `¬ problem_spec_serverStartup skip (implementation … skip)`
    at a concrete boolean, closed by `decide`. The spec and impl are both fully
    transparent (no opaque callee), so `decide` computes both lists. It ELABORATES
    against a rival whose result diverges from the spec at `skip`, and FAILS on gold
    (which satisfies the spec at every input)."""
    return (
        f"example : ¬ problem_spec_serverStartup {skip}\n"
        f"    (implementation_serverStartup {skip}) := by\n"
        f"  unfold problem_spec_serverStartup implementation_serverStartup tailSteps\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ----- soundness / positive control -----
    {
        "id": "pos-prefix-as-value",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _INIT_AND_PREFIX, _POS_PREFIX_VALUE),
        "rationale": (
            "structurally-different but CORRECT impl: the gated prefix is built by "
            "initialising the accumulator from a conditional VALUE (`if skipChecks "
            "then [] else [announce, run]`) rather than by a conditional append "
            "statement. The result is identical on both inputs. The frozen "
            "`theorem correct_serverStartup` statement is kept byte-identical and its "
            "`cases skipChecks <;> rfl` proof still closes (each branch reduces to a "
            "concrete list). If it FAILS => SPEC-TOO-STRONG (a faithful, "
            "structurally-different correct impl rejected)."
        ),
    },
    # ----- admissibility (added by the second audit) -----
    {
        "id": "admiss-f2p-skip-requested",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_INTRO, _ADMISS_HAVES + _P_INTRO),
        "rationale": (
            "the obligation must be SATISFIABLE at the F2P-shaped input — a skip "
            "REQUESTED — and not merely in the abstract. The frozen theorem is "
            "unguarded, so there is no precondition hypothesis to attack with a "
            "nagini-style call-site probe; the analogue on this total carrier is "
            "the obligation being unsatisfiable at exactly that input, which this "
            "case discharges BY EVALUATION as two ground `have`s (the spec "
            "predicate at `skipChecks = true`, plus the concrete schedule that "
            "input produces, so the admission cannot be read off without "
            "computing the gated branch) before closing the frozen obligation "
            "verbatim. Both `have`s are load-bearing, measured: the same prefix "
            "FAILS against weak-skip-not-honored, weak-gate-inverted, "
            "weak-drop-serve and weak-always-skip. If it FAILS => "
            "PRECOND-TOO-STRONG (the obligation is unsatisfiable at a normal, "
            "acceptance-shaped input). The theorem statement is byte-identical "
            "and no new declaration is introduced."
        ),
    },
    # ----- uniqueness / reject rivals -----
    {
        "id": "weak-skip-not-honored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PREFIX, _WEAK_NOTHONORED),
        "refinement": (
            "this IS the pre-change routine: the announce+run system-check prefix is "
            "emitted UNCONDITIONALLY, with no gate on the skip control. Its faithful "
            "real counterpart is the unchanged repo, which still performs the checks "
            "when the skip control is set — exactly the FAIL_TO_PASS test, which "
            "asserts that under a skip request the announcement is ABSENT and the "
            "check is NOT performed. It does NOT resolve, so a verifying rival here "
            "would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition on the skipChecks=true sub-domain: the "
            "spec pins the result to the tail alone `[]++tail`, but the rival prepends "
            "the two-step prefix. Attacks the gated-prefix clause from the over-emit "
            "side and varies the skipChecks binder at `true`. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # skip=true: gold => tail; rival => [announce,run]++tail.
        "witness": _wit("true"),
    },
    {
        "id": "weak-skip-emits-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PREFIX, _WEAK_RUNUNDERSKIP),
        "refinement": (
            "a real patch that guarded ONLY the announcement but left the check run "
            "outside the guard would still perform the checks under a skip request. "
            "The FAIL_TO_PASS test asserts the check is NOT performed when the skip "
            "control is set — hiding the banner alone does not satisfy it — so this "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition on skipChecks=true: the spec pins the "
            "result to the tail alone, but the rival emits `[run]++tail`. Attacks the "
            "gated-prefix clause (the run step must be inside the gate too) and varies "
            "the binder at `true`. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # skip=true: gold => tail; rival => [run]++tail.
        "witness": _wit("true"),
    },
    {
        "id": "weak-wrong-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PREFIX, _WEAK_WRONGORDER),
        "refinement": (
            "a real patch that emitted the check run before the announcement reverses "
            "the observable order of the two system-check steps. The announcement is "
            "meant to precede the run it announces, and the spec pins the exact "
            "emission order, so this diverges from the documented start-up sequence. "
            "SCOPE OF THIS CLAIM (corrected by audit): the acceptance test observes "
            "only the PRESENCE of the announcement in captured output and whether the "
            "check step ran; it isolates the check step behind a stand-in and so "
            "records no relative order between the two. This rival is therefore a "
            "genuine divergence from the SPECIFIED behaviour that the acceptance test "
            "does not by itself distinguish — it is a uniqueness attack on the "
            "prefix-ORDER clause, NOT a verify-does-not-resolve rival. Do not read it "
            "as one; the two rivals that do fail the acceptance test are "
            "weak-skip-not-honored / weak-skip-emits-run (over-emit under a skip "
            "request) and weak-always-skip / weak-gate-inverted (under-emit when no "
            "skip is requested)."
        ),
        "rationale": (
            "REJECTED by the postcondition on skipChecks=false: the spec pins the "
            "prefix to `[announce, run]`, but the rival emits `[run, announce]`. "
            "Attacks the prefix-ORDER clause and varies the binder at `false`. If it "
            "VERIFIES => SPEC-TOO-WEAK on the ordering sub-domain."
        ),
        # skip=false: gold => [announce,run]++tail; rival => [run,announce]++tail.
        "witness": _wit("false"),
    },
    {
        "id": "weak-drop-migration",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PREFIX_AND_MIG, _WEAK_DROPMIG),
        "refinement": (
            "a real patch that folded the always-on migration re-check inside the "
            "skip guard would drop it under a skip request. That step is deliberately "
            "performed regardless of the control, and dropping it changes start-up "
            "behaviour: the pending-migration warning silently vanishes whenever a "
            "skip is requested. SCOPE OF THIS CLAIM (corrected by audit): the "
            "acceptance test replaces that step with a stand-in and never asserts the "
            "stand-in was invoked, and the suite's other coverage of it calls it "
            "directly rather than through the start-up routine — so no test in the "
            "recorded sets observes its omission from the routine. This rival is a "
            "genuine divergence from the SPECIFIED behaviour (the spec pins the tail, "
            "per the frame directive that unchanged outputs be pinned in both "
            "branches) that the recorded tests do not by themselves distinguish. It is "
            "a uniqueness attack on the fixed-tail clause, NOT a "
            "verify-does-not-resolve rival."
        ),
        "rationale": (
            "REJECTED by the postcondition on skipChecks=true: the always-on tail "
            "must begin with the migration re-check, but the rival omits it, yielding "
            "`[banner, serve]` where the spec requires `[checkMigrations, banner, "
            "serve]`. Attacks the fixed-tail clause (a step this carrier models that "
            "nagini's schedule did not distinguish here) and varies the binder at "
            "`true`. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # skip=true: gold => [checkMigrations,banner,serve]; rival => [banner,serve].
        "witness": _wit("true"),
    },
    {
        "id": "weak-drop-serve",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SERVE_AND_RET, _WEAK_DROPSERVE),
        "refinement": (
            "a real patch that omitted the final always-on step would never reach the "
            "point of serving requests — a total functional regression of the command, "
            "on every input, regardless of the control. SCOPE OF THIS CLAIM (corrected "
            "by audit): the acceptance test replaces that step with a stand-in and "
            "never asserts the stand-in was invoked, and every other recorded test "
            "either substitutes the routine's server-launch entry point or never "
            "enters the routine at all — so no test in the recorded sets observes the "
            "omission, even though a user would immediately. This rival is a genuine "
            "divergence from the SPECIFIED behaviour (the spec pins the tail in both "
            "branches) that the recorded tests do not by themselves distinguish: a "
            "uniqueness attack on the fixed-tail clause, NOT a "
            "verify-does-not-resolve rival."
        ),
        "rationale": (
            "REJECTED by the postcondition: the fixed tail must end with the final "
            "step, but the rival drops it. Attacks the fixed-tail clause (a tail step "
            "this carrier models that nagini's schedule did not carry) and varies the "
            "binder at `false`. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # skip=false: gold => [announce,run,checkMigrations,banner,serve];
        #             rival => [announce,run,checkMigrations,banner].
        "witness": _wit("false"),
    },
    {
        "id": "weak-tail-reorder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BANNER_SERVE, _WEAK_TAILREORDER),
        "refinement": (
            "a real patch that swapped the last two always-on steps reverses their "
            "fixed emission order, so the banner announcing where the server can be "
            "reached would be written only after the server had already begun serving. "
            "SCOPE OF THIS CLAIM (corrected by audit): both steps are replaced by "
            "stand-ins or unreached in the recorded tests, which assert nothing about "
            "their relative order, so no recorded test observes the swap. This rival is "
            "a genuine divergence from the SPECIFIED behaviour (the spec pins the tail "
            "order in both branches) that the recorded tests do not by themselves "
            "distinguish: a uniqueness attack on the fixed-tail ORDER clause, NOT a "
            "verify-does-not-resolve rival."
        ),
        "rationale": (
            "REJECTED by the postcondition: the fixed tail pins the last two steps in "
            "a set order, but the rival emits them reversed. Attacks the fixed-tail "
            "ORDER clause and varies the binder at `false`. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # skip=false: gold => [...,banner,serve]; rival => [...,serve,banner].
        "witness": _wit("false"),
    },
    # ----- added by AUDIT: the under-emit half of the gated-prefix clause -----
    {
        "id": "weak-always-skip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PREFIX_NL, _WEAK_ALWAYSSKIP),
        "refinement": (
            "a real patch that suppressed the system-check step UNCONDITIONALLY — "
            "treating the control as always set — would never perform the checks even "
            "when the caller asked for them. This DOES fail the acceptance test, on its "
            "no-skip half: that half asserts the announcement IS present in captured "
            "output and that the check step DID run, and both are absent here. It is "
            "therefore a true verify-does-not-resolve rival if it were to verify. Added "
            "by audit because both pre-existing prefix-presence rivals diverged only by "
            "OVER-emitting under a skip request, leaving the opposite direction — the "
            "prefix must still appear when no skip is requested — unattacked."
        ),
        "rationale": (
            "REJECTED by the postcondition on the skipChecks=false sub-domain: the spec "
            "requires the two-step prefix ahead of the tail, but the rival emits the "
            "tail alone. Attacks the gated-prefix clause from the UNDER-emit side and "
            "varies the skipChecks binder at `false` — the complementary point to the "
            "existing rivals, which all diverge at `true`. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # skip=false: gold => [announce,run]++tail; rival => tail.
        "witness": _wit("false"),
    },
    {
        "id": "weak-gate-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _PREFIX, _WEAK_GATEINVERTED),
        "refinement": (
            "a real patch that inverted the guard's polarity would perform the "
            "system-check step exactly when the caller asked to skip it, and skip it "
            "exactly when the caller did not — the control wired backwards. This DOES "
            "fail the acceptance test, on BOTH of its halves simultaneously (under a "
            "skip request the announcement is present and the check runs, when both must "
            "be absent; with no skip request both are absent, when both must be "
            "present). A true verify-does-not-resolve rival, and the one most directly "
            "opposed to the modeled control's meaning. Added by audit."
        ),
        "rationale": (
            "REJECTED by the postcondition at BOTH points of the input domain: the spec "
            "ties the prefix's presence to `skipChecks` being false, and the rival ties "
            "it to `skipChecks` being true. Attacks the gate's DIRECTION rather than its "
            "placement or the order of its contents; the witness is stated at `true`, "
            "where the rival over-emits, and it is equally refutable at `false`. If it "
            "VERIFIES => SPEC-TOO-WEAK on the clause that carries the whole change."
        ),
        # skip=true: gold => tail; rival => [announce,run]++tail.
        "witness": _wit("true"),
    },
]


# No @ContractOnly axioms and no opaque callees: the routine's behavior is modeled
# DEEPLY as a gated list construction over the transparent StartupAction carrier, so
# the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
