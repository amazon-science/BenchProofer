#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13809 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below. The impl carries
no contract calls inside the impl markers, so nothing needed stripping; the
pure-region action-code constants are copied over as plain module constants.
The model uses only List[int] (no PSeq in the impl), so no sequence shim is
needed. There are no @ContractOnly callees.

ORACLE: the REAL patched repo command class, imported from /testbed (the gate
applies patch.diff before this script runs; PYTHONPATH=/testbed):
`django.core.management.commands.runserver.Command`.

  Leg 1 (offers_skip_request): build the command's real invocation parser via
  `Command.create_parser` and observe whether the parsed namespace carries the
  skip-request destination — both with the request token absent and present.
  Per mapping.md, "the option is registered <-> the parser offers the request";
  the parsed namespace carrying the destination (default False / True with the
  token) is the runtime observable of that registration.

  Leg 2 (startup_action_schedule): run the REAL `Command.inner_run` with the
  real parsed options and record the schedule of observable start-up actions
  at their boundaries, per the mapping.md bijection:
    - a write to the command's output stream during the observed start-up
      window  -> ACTION_ANNOUNCE_VALIDATION
    - a `check` invocation                    -> ACTION_RUN_VALIDATION
    - a `check_migrations` invocation         -> ACTION_MIGRATION_RECHECK
  The recorder raises a sentinel from the migration re-check boundary, ending
  the observed window there (the model's schedule covers exactly the start-up
  actions up to and including that re-check; the later banner writes and the
  serving loop are outside the modeled behaviour). The boundary callables are
  instance-level recorders, so the real inner_run control flow — including
  which of them it reaches and in what order — is what is exercised.

Type bridge (mapping.md section 2): the invocation-level input is whether the
skip token is on the command line; the model carrier is the bool `skip_checks`.
We drive the REAL parser with/without the token and feed the resulting parsed
namespace to the real inner_run, while the shadow gets the same bool.

Input domain: the model has no Requires, and the input is a single bool, so
the domain is exhaustively {False, True}. Boundary pass enumerates both;
a deterministic fuzz loop then re-draws bools to honour the >=1e5-input
convention. Pinned fuzz seed: 13809 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import random
import sys

SEED = 13809
N_FUZZ = 100_000


# --- pure region of model.py (constants), copied over ------------------------

ACTION_ANNOUNCE_VALIDATION = 1   # announce that the validation pass is running
ACTION_RUN_VALIDATION = 2        # perform the validation pass
ACTION_MIGRATION_RECHECK = 3     # re-check pending data-shape migrations


# --- the impl regions of model.py, verbatim ----------------------------------

def offers_skip_request():
    return True


def startup_action_schedule(skip_checks):
    schedule = []  # type: List[int]
    if not skip_checks:
        # The suppressible validation pass: announce, then run it (as a unit).
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
        schedule.append(ACTION_RUN_VALIDATION)
    # The migration re-check is not part of the suppressible validation pass; it
    # always runs.
    schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule


# --- oracle plumbing ----------------------------------------------------------

class _EndOfObservedWindow(Exception):
    """Raised by the migration re-check recorder: the modeled start-up window
    ends with that action; everything after it is outside the model."""


class _RecordingStream:
    """File-like sink for the command's output wrapper; every write during the
    observed window is the announcement-action observable (mapping.md)."""

    def __init__(self, schedule):
        self._schedule = schedule

    def write(self, msg):
        self._schedule.append(ACTION_ANNOUNCE_VALIDATION)

    def flush(self):
        pass

    def isatty(self):
        return False


def _configure_django():
    """Minimal settings so the command class can be instantiated; the boundary
    callables that would touch the database or the app registry are replaced
    by recorders, so no apps/DB configuration is needed."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True, ALLOWED_HOSTS=["*"], INSTALLED_APPS=[])
        django.setup()


def real_parsed_options(command_cls, pass_token):
    """Parse the command's real invocation parser with/without the skip token.
    Returns (namespace-dict or None-if-rejected)."""
    parser = command_cls().create_parser("manage.py", "runserver")
    argv = ["--skip-checks"] if pass_token else []
    try:
        return vars(parser.parse_args(argv))
    except (SystemExit, Exception):
        # the command's parser raises its own error type when not invoked
        # from a real command line; either way the invocation was rejected
        return None


def real_startup_schedule(command_cls, options):
    """Run the REAL inner_run with recorder boundaries; return the observed
    action-code schedule for the modeled start-up window."""
    schedule = []
    cmd = command_cls(stdout=_RecordingStream(schedule),
                      stderr=_RecordingStream([]))

    def _record_check(*args, **kwargs):
        schedule.append(ACTION_RUN_VALIDATION)

    def _record_check_migrations(*args, **kwargs):
        schedule.append(ACTION_MIGRATION_RECHECK)
        raise _EndOfObservedWindow()

    cmd.check = _record_check
    cmd.check_migrations = _record_check_migrations
    try:
        cmd.inner_run(**dict(options))
    except _EndOfObservedWindow:
        pass
    return schedule


def main():
    _configure_django()
    from django.core.management.commands.runserver import Command

    failures = 0
    checked = 0

    # --- Leg 1: offers_skip_request vs the real parser exposure --------------
    ns_absent = real_parsed_options(Command, False)
    ns_present = real_parsed_options(Command, True)
    real_offers = (
        ns_absent is not None and "skip_checks" in ns_absent
        and ns_present is not None and ns_present.get("skip_checks") is True
        and ns_absent.get("skip_checks") is False
    )
    if real_offers != offers_skip_request():
        failures += 1
        print("DISAGREE offers_skip_request: real=%r shadow=%r "
              "(ns_absent=%r ns_present=%r)"
              % (real_offers, offers_skip_request(), ns_absent, ns_present))
    checked += 1

    if ns_absent is None or ns_present is None:
        print("checked=%d disagreements=%d (parser rejected an invocation; "
              "schedule leg not reachable)" % (checked, failures))
        print("status=fail")
        return 1

    options_by_flag = {False: ns_absent, True: ns_present}

    # --- Leg 2: startup_action_schedule vs the real inner_run ---------------
    def compare(skip_checks, tag):
        opts = options_by_flag[skip_checks]
        real = real_startup_schedule(Command, opts)
        shadow = startup_action_schedule(skip_checks)
        if real != shadow:
            print("DISAGREE %s skip_checks=%r: real=%r shadow=%r"
                  % (tag, skip_checks, real, shadow))
            return 1
        return 0

    # Boundary: the input domain is a single bool — enumerate it exhaustively.
    for skip_checks in (False, True):
        failures += compare(skip_checks, "boundary")
        checked += 1

    # Fuzz: deterministic re-draws over the bool domain (>=1e5 inputs), each
    # driving the REAL inner_run afresh. Pinned seed.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        skip_checks = rng.random() < 0.5
        failures += compare(skip_checks, "fuzz")
        checked += 1
        if failures:
            break

    if failures:
        print("checked=%d disagreements=%d" % (checked, failures))
        print("status=fail")
        return 1
    print("checked=%d disagreements=0" % checked)
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
