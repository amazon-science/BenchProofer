"""properties.py — PBT falsification battery for django__django-13809.

NOT a Nagini module; a record of adversarially-reasoned cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants that SHARE the frozen spec byte-for-byte (region-surgery edits
ONLY inside a `# impl-start`/`# impl-end` region) and differ only in the impl;
they are checked by Nagini verify + markers.same_spec.

Defended surface (read model.py):
  * offers_skip_request() -> bool. No inputs. Post: Ensures(Result()) — must
    return True. There is no @Pure answer-key to echo; the only sequence-of-
    truth here is the constant True, so the cheapest HONEST impl IS the gold
    one. The reject attack is the wrong-direction constant (return False =
    model_prepatch_2: command stops offering --skip-checks).
  * startup_action_schedule(skip_checks: bool) -> List[int]. ONE input,
    `skip_checks`, a primitive `bool` passed BY VALUE — there is no Acc(x,1/2)
    read-only reference parameter anywhere in this bundle, so the frame-mutation
    class is N/A (see 'assessment' in the structured return; there is no
    half-permission input to overwrite). The postcondition pins the output
    EXACTLY for both branches via two grounded `ToSeq(Result()) == PSeq(...)`
    clauses plus length clauses — the schedule is a total function of the input,
    grounded in literal action codes tied to the branch condition. No oracle
    echo is possible; uniqueness attacks must therefore be partial-domain
    divergences on the two-point input domain {True, False}.

No @ContractOnly axioms are consumed (axioms: [] in meta.json). The single
deep-model reference is the argparse store_true exposure + inner_run gate,
already validated by axiom_check.py (G-AX) against the REAL stdlib argparse.
We reproduce that check as an AXIOM_TESTS containment/soundness probe so the
A-reference is re-run under PBT too.
"""
from pathlib import Path

INSTANCE = "django__django-13809"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. The two impl regions (verbatim from model.py) we mutate.
# ---------------------------------------------------------------------------

# offers_skip_request impl region (between its impl-start/impl-end)
_OFFERS_IMPL = """    # impl-start
    return True
    # impl-end"""

# startup_action_schedule impl region (between its impl-start/impl-end)
_SCHED_IMPL = """    # impl-start
    schedule = []  # type: List[int]
    if not skip_checks:
        # The suppressible validation pass: announce, then run it (as a unit).
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
        schedule.append(ACTION_RUN_VALIDATION)
    # The migration re-check is not part of the suppressible validation pass; it
    # always runs.
    schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule
    # impl-end"""


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-different CORRECT impls.
# ===========================================================================

# pos-control-schedule: invert the branch — handle the skip case in the `if`
# and the no-skip case in the `else`. Builds the identical literal sequences
# (no fold/induction lemma needed — only literal appends), so the gold proof
# obligations are preserved. If a faithful correct impl in a different
# structural shape cannot verify => SPEC-TOO-STRONG.
_POS_SCHED = """    # impl-start
    schedule = []  # type: List[int]
    if skip_checks:
        # Skip request in force: only the (always-on) migration re-check runs.
        schedule.append(ACTION_MIGRATION_RECHECK)
    else:
        # No skip request: announce, run validation, then the migration re-check.
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
        schedule.append(ACTION_RUN_VALIDATION)
        schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule
    # impl-end"""

# pos-control-offers: return a different-shaped constant True. Must verify
# against Ensures(Result()).
_POS_OFFERS = """    # impl-start
    flag = (1 == 1)  # type: bool
    return flag
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY — confirm the (empty) precondition admits both F2P-shaped
# bool inputs by self-calling the modeled function from inside the impl region
# and asserting the pinned postcondition holds for each. If the call site
# cannot establish the Requires for a normal input => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS_SCHED = """    # impl-start
    sched_skip = startup_action_schedule(True)
    Assert(ToSeq(sched_skip) == PSeq(ACTION_MIGRATION_RECHECK))
    sched_noskip = startup_action_schedule(False)
    Assert(ToSeq(sched_noskip) == PSeq(ACTION_ANNOUNCE_VALIDATION,
                                       ACTION_RUN_VALIDATION,
                                       ACTION_MIGRATION_RECHECK))
    schedule = []  # type: List[int]
    if not skip_checks:
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
        schedule.append(ACTION_RUN_VALIDATION)
    schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule
    # impl-end"""


# ===========================================================================
# UNIQUENESS / REJECT RIVALS — same spec, wrong impl, MUST NOT verify.
# Each carries the refinement argument that its faithful real patch would NOT
# resolve the F2P (test_skip_checks) / P2P.
# ===========================================================================

# weak-skip-not-honored (= model_prepatch.py behaviour): emit the full
# validation pass regardless of the skip request. Fails clause (2a)
# Implies(skip_checks, ToSeq(Result()) == PSeq(MIGRATION_RECHECK)) and the
# length-1 clause.
_WEAK_NOTHONORED = """    # impl-start
    schedule = []  # type: List[int]
    # WRONG: announce + run emitted unconditionally (no skip gate).
    schedule.append(ACTION_ANNOUNCE_VALIDATION)
    schedule.append(ACTION_RUN_VALIDATION)
    schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule
    # impl-end"""

# weak-skip-emits-run: under a skip request, suppress the ANNOUNCE but still
# RUN the validation. Fails clause (2a) (result would be [RUN, MIGRATION] not
# [MIGRATION]).
_WEAK_RUNUNDERSKIP = """    # impl-start
    schedule = []  # type: List[int]
    if not skip_checks:
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
    # WRONG: the validation run is emitted even under a skip request (the gate
    # was placed only around the announcement).
    schedule.append(ACTION_RUN_VALIDATION)
    schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule
    # impl-end"""

# weak-drop-migration: under a skip request, drop the migration re-check too
# (put it inside the suppressible pass). Fails clause (2a) / the length-1 clause
# (result [] not [MIGRATION]).
_WEAK_DROPMIG = """    # impl-start
    schedule = []  # type: List[int]
    if not skip_checks:
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
        schedule.append(ACTION_RUN_VALIDATION)
        # WRONG: migration re-check folded into the suppressible pass.
        schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule
    # impl-end"""

# weak-wrong-order: in the no-skip branch, run the validation BEFORE announcing
# it. Fails clause (2b) exact-sequence (RUN, ANNOUNCE, MIGRATION) != (ANNOUNCE,
# RUN, MIGRATION).
_WEAK_WRONGORDER = """    # impl-start
    schedule = []  # type: List[int]
    if not skip_checks:
        # WRONG: run the validation before announcing it.
        schedule.append(ACTION_RUN_VALIDATION)
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
    schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule
    # impl-end"""

# weak-offers-false (= model_prepatch_2.py behaviour): this command stops
# offering the skip request. Fails Ensures(Result()).
_WEAK_OFFERSFALSE = """    # impl-start
    return False
    # impl-end"""


SPEC_TESTS = [
    # ----- soundness / positive controls -----
    {
        "id": "pos-control-schedule",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _SCHED_IMPL, _POS_SCHED),
        "rationale": "branch-inverted but behaviourally identical impl "
                     "(skip-case in the `if`, full-case in the `else`); builds "
                     "the same literal action sequences with only literal "
                     "appends (no fold/induction lemma needed), so the gold "
                     "proof obligations still discharge. Must verify, else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-offers",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _OFFERS_IMPL, _POS_OFFERS),
        "rationale": "a different-shaped constant True ((1==1) bound to a typed "
                     "local) must satisfy Ensures(Result()); else SPEC-TOO-STRONG.",
    },
    # ----- admissibility -----
    {
        "id": "admiss-schedule",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _SCHED_IMPL, _ADMISS_SCHED),
        "rationale": "self-calls startup_action_schedule on both F2P-shaped bool "
                     "inputs (True/False) and asserts the pinned postconditions "
                     "hold; the (empty) precondition must admit both. If the "
                     "call site cannot establish Requires => PRECOND-TOO-STRONG.",
    },
    # ----- uniqueness / reject rivals -----
    {
        "id": "weak-skip-not-honored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SCHED_IMPL, _WEAK_NOTHONORED),
        "refinement": "faithful real patch = the PRE-PATCH inner_run (the "
                      "announcement + self.check(display_num_errors=True) run "
                      "UNCONDITIONALLY, no `if not options['skip_checks']` "
                      "gate). This is exactly model_prepatch.py. test_skip_checks "
                      "(ManageRunserver) asserts that with skip_checks=True the "
                      "'Performing system checks' message is absent and check is "
                      "NOT called — an ungated impl prints/calls check, so the "
                      "F2P FAILS. verify here would be a true verify-not-resolve "
                      "break.",
        "rationale": "fails postcondition clause (2a) "
                     "Implies(skip_checks, ToSeq(Result())==PSeq(MIGRATION_RECHECK)) "
                     "and the Implies(skip_checks, len==1) clause: under skip it "
                     "produces [ANNOUNCE,RUN,MIGRATION] (len 3).",
    },
    {
        "id": "weak-skip-emits-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SCHED_IMPL, _WEAK_RUNUNDERSKIP),
        "refinement": "faithful real patch guards ONLY the "
                      "self.stdout.write('Performing system checks...') by "
                      "`if not options['skip_checks']` but leaves "
                      "self.check(display_num_errors=True) OUTSIDE the guard, so "
                      "the validation still runs under --skip-checks. "
                      "test_skip_checks asserts check is NOT called when "
                      "skip_checks=True, so the F2P FAILS — the whole point of "
                      "the change is to skip the system checks, not just hide the "
                      "banner.",
        "rationale": "fails clause (2a): under skip it produces "
                     "[RUN,MIGRATION] (ToSeq != PSeq(MIGRATION_RECHECK), len 2 "
                     "!= 1).",
    },
    {
        "id": "weak-drop-migration",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SCHED_IMPL, _WEAK_DROPMIG),
        "refinement": "faithful real patch folds self.check_migrations() INSIDE "
                      "the `if not options['skip_checks']` guard, so the always-on "
                      "migration re-check is dropped under --skip-checks. The "
                      "gold deliberately leaves check_migrations() outside the "
                      "guard (the comment 'Need to check migrations here, so "
                      "can't use the requires_migrations_check attribute'); "
                      "dropping it changes start-up behaviour and the migration "
                      "warning would silently vanish — not the documented "
                      "behaviour. The schedule the test/spec observes diverges "
                      "under skip.",
        "rationale": "fails clause (2a) / Implies(skip_checks, len==1): under "
                     "skip it produces [] (empty), ToSeq([]) != "
                     "PSeq(MIGRATION_RECHECK).",
    },
    {
        "id": "weak-wrong-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SCHED_IMPL, _WEAK_WRONGORDER),
        "refinement": "faithful real patch swaps the two guarded statements: "
                      "self.check(display_num_errors=True) BEFORE "
                      "self.stdout.write('Performing system checks...'). The "
                      "announcement is meant to precede the validation run (it "
                      "announces that validation IS being performed); reversing "
                      "the order means the banner prints after the check output, "
                      "changing the observable start-up action ordering. The "
                      "spec pins the exact emission order.",
        "rationale": "fails clause (2b) exact-sequence: no-skip yields "
                     "[RUN,ANNOUNCE,MIGRATION], ToSeq != "
                     "PSeq(ANNOUNCE,RUN,MIGRATION).",
    },
    {
        "id": "weak-offers-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _OFFERS_IMPL, _WEAK_OFFERSFALSE),
        "refinement": "faithful real patch = the PRE-PATCH add_arguments (this "
                      "command does NOT register --skip-checks on its own "
                      "parser; it sets requires_system_checks=[] so the common "
                      "BaseCommand.create_parser machinery never adds the option "
                      "for it). This is exactly model_prepatch_2.py. Without the "
                      "option registered, `runserver --skip-checks` is an "
                      "unrecognised-argument error and skip can never be set, so "
                      "test_skip_checks (which invokes with --skip-checks) FAILS.",
        "rationale": "fails Ensures(Result()): returns False where the spec "
                     "requires True (the skip request must be offered "
                     "unconditionally).",
    },
]


# ===========================================================================
# AXIOM LANE — no @ContractOnly axioms (meta.axioms == []). The single
# A-reference (argparse store_true exposure + the inner_run gate) is validated
# by axiom_check.py against the REAL stdlib argparse. We re-run that obligation
# here as both a soundness and a containment probe so the deep-model reference
# is exercised under PBT. The probes import ONLY the standard library, so they
# run identically in the instance Docker image (apply_gold=True is harmless:
# argparse is stdlib and the gold add_arguments is mirrored inline).
# ===========================================================================

# Embed the bundle's own axiom_check.py source at load time (HOST read) so the
# probe is self-contained in-container (the runner mounts only the probe).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(
    encoding="utf-8")

# axiom-soundness probe: run the bundle's real-argparse oracle end-to-end. It
# exits 0 iff (R1) the store_true --skip-checks option is exposed/defaulted as
# the deep model assumes AND (R2) the real inner_run start-up gate over BOTH
# token values equals startup_action_schedule. This IS the soundness check:
# the real callee (argparse + the gold gate) must match the model's Ensures.
_PROBE_SOUNDNESS = (
    "# axiom-soundness probe for django__django-13809 (A-reference).\n"
    "# Runs the bundle's real-argparse oracle (axiom_check.main): asserts the\n"
    "# real store_true exposure/default + the real inner_run gate over both\n"
    "# token values match the deep model. Exit 0 iff the obligation holds.\n"
    + _AXIOM_CHECK_SRC
)

# axiom-containment probe: the model's startup_action_schedule can only pass a
# 2-point bool domain {False, True} to the gate, and offers_skip_request reaches
# the parser with no token / the --skip-checks token. We enumerate EXACTLY those
# caller-reachable inputs against the real argparse and assert each yields a
# defined, in-domain parsed value (store_true => bool, present in namespace) and
# the gate's emitted schedule is well-defined. A reachable input outside the
# parser's accepted domain would be AXIOM-TOO-WEAK-FOR-CALLER.
_PROBE_CONTAINMENT = r'''# axiom-containment probe for django__django-13809.
# The deep model's caller reaches the argparse store_true callee with EXACTLY
# two argv shapes: [] (token absent) and ['--skip-checks'] (token present),
# corresponding to skip_checks in {False, True}. Assert each caller-reachable
# input lies in the parser's accepted domain (parses without error, yields a
# bool skip_checks present in the namespace, gate schedule well-defined).
import argparse
import contextlib
import io
import sys

def build_real_parser():
    p = argparse.ArgumentParser(prog="runserver")
    p.add_argument('--ipv6', '-6', action='store_true', dest='use_ipv6')
    p.add_argument('--nothreading', action='store_false', dest='use_threading')
    p.add_argument('--noreload', action='store_false', dest='use_reloader')
    p.add_argument('--skip-checks', action='store_true', help='Skip system checks.')
    return p

# EXACTLY the caller-reachable argv shapes (the 2-point input domain).
REACHABLE = {False: [], True: ['--skip-checks']}
ACTION_ANNOUNCE, ACTION_RUN, ACTION_MIG = 1, 2, 3

failures = 0
for expected_skip, argv in REACHABLE.items():
    parser = build_real_parser()
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            ns = vars(parser.parse_args(argv))
    except SystemExit:
        failures += 1
        print("OUT-OF-DOMAIN: argv=%r rejected by the real parser" % (argv,))
        continue
    if 'skip_checks' not in ns:
        failures += 1
        print("OUT-OF-DOMAIN: skip_checks absent for argv=%r ns=%r" % (argv, ns))
        continue
    val = ns['skip_checks']
    if not isinstance(val, bool):
        failures += 1
        print("OUT-OF-DOMAIN: skip_checks not bool for argv=%r: %r" % (argv, val))
        continue
    if val != expected_skip:
        failures += 1
        print("DOMAIN-MISMATCH: argv=%r expected skip=%r got %r" % (argv, expected_skip, val))
        continue
    # gate schedule well-defined over this reachable input
    sched = []
    if not val:
        sched.append(ACTION_ANNOUNCE)
        sched.append(ACTION_RUN)
    sched.append(ACTION_MIG)
    print("COVERED: argv=%r -> skip_checks=%r schedule=%r" % (argv, val, sched))

if failures:
    print("CONTAINMENT FAIL: %d caller-reachable input(s) outside the argparse domain" % failures)
    sys.exit(1)
print("CONTAINMENT OK: both caller-reachable inputs ({} , ['--skip-checks']) lie in the real argparse store_true domain")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-argparse-gate",
        "axiom": "argparse store_true exposure + inner_run start-up gate (A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUNDNESS,
        "rationale": "the real stdlib argparse store_true exposure/default and "
                     "the real inner_run gate (announce+run iff not skip_checks; "
                     "migration re-check always) must match the deep model's "
                     "Ensures over both token values; if the real callee "
                     "disagrees => AXIOM-UNSOUND. Probe is the bundle's own "
                     "axiom_check.py (stdlib argparse only).",
    },
    {
        "id": "ax-cover-argparse-domain",
        "axiom": "argparse store_true exposure + inner_run start-up gate (A-reference)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "the model reaches the store_true callee with EXACTLY the "
                     "2-point argv domain {[], ['--skip-checks']}; both must be "
                     "accepted by the real parser and yield a bool skip_checks "
                     "in the namespace. A reachable argv outside the accepted "
                     "domain => AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
