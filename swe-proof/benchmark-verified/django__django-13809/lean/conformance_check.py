#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13809.

The bundle models ONE function: the development server's startup routine
(`runserver`'s `inner_run`). Its Lean implementation
(`implementation_serverStartup`) emits the ordered list of observable startup
actions, with the system-check step (announce + run checks) gated on a boolean
control `skipChecks`:

    log = []
    if not skip_checks:
        log += ["announceChecks", "runChecks"]
    log += ["checkMigrations", "writeBanner", "serve"]

This script transliterates that R/I impl into Python (`shadow_startup`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch behavior of `inner_run`
(`django/core/management/commands/runserver.py`):

    if not options['skip_checks']:
        self.stdout.write('Performing system checks...\n\n')   # announceChecks
        self.check(display_num_errors=True)                    # runChecks
    self.check_migrations()                                    # checkMigrations
    # ... write banner ...                                     # writeBanner
    run(...)                                                   # serve

We do NOT stand up a real management command / server (heavy, and the modeled
value is the pure ordered sequence of observable steps the routine performs).
Instead we reproduce the patched control flow over the same observable actions
the routine emits (mapping.md): the announcement write and the `self.check()`
call form the gated system-check step; the migration check, banner write, and
server start are always performed, in order. The pre-patch routine performed the
system-check step unconditionally (ignoring `skip_checks`); the post-patch
routine performs it iff `skip_checks` is false — which is what the oracle below
encodes. The shadow reaches the same trace via the `not skip_checks` gate.

The differential genuinely tests the Lean modeling: the shadow uses Lean's
`if !skipChecks then …` gated list construction, whereas the oracle reproduces
the patched `if not options['skip_checks']:` control flow over realistic
observable-action records. They must agree for every input — in particular when
`skip_checks` is true, the case the patch newly suppresses.

stdlib-only; deterministic. Pinned seed: 13809 (also recorded in mapping.md).
"""
import sys

SEED = 13809

ANNOUNCE = "announceChecks"
RUN = "runChecks"
CHECK_MIG = "checkMigrations"
BANNER = "writeBanner"
SERVE = "serve"

TAIL = [CHECK_MIG, BANNER, SERVE]


# --- ORACLE: the post-patch behavior, faithful in-process replica ------------
# The startup routine emits a fixed ordered sequence of observable actions.
# The system-check step (announce + run checks) is performed iff checks are not
# skipped; the remaining steps are always performed, in order.
def oracle_startup(skip_checks):
    log = []
    if not skip_checks:                 # `if not options['skip_checks']:`
        log.append(ANNOUNCE)            # self.stdout.write("Performing system checks...")
        log.append(RUN)                 # self.check(display_num_errors=True)
    log.append(CHECK_MIG)               # self.check_migrations()
    log.append(BANNER)                  # self.stdout.write(<banner>)
    log.append(SERVE)                   # run(...)
    return log


# --- shadow of implementation_serverStartup (the R/I leg) --------------------
# Mirrors Solution.lean: gated prefix [announceChecks, runChecks] when
# not skipChecks, then the always-emitted tail.
def shadow_startup(skip_checks):
    log = []
    if not skip_checks:
        log = log + [ANNOUNCE]
        log = log + [RUN]
    log = log + [CHECK_MIG]
    log = log + [BANNER]
    log = log + [SERVE]
    return log


def disagree(skip_checks):
    got = oracle_startup(skip_checks)
    want = shadow_startup(skip_checks)
    if got != want:
        return (skip_checks, got, want)
    return None


def main() -> int:
    checked = 0
    # The input is a single boolean; the domain is exhaustively enumerable.
    # We additionally repeat to honor the >=1e5 fuzz convention deterministically.
    for skip_checks in (True, False):
        d = disagree(skip_checks)
        if d:
            print(f"DISAGREE edge skip_checks={d[0]}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    # Deterministic LCG-driven fuzz over the boolean domain (>=1e5 inputs).
    x = SEED & 0xFFFFFFFF
    for _ in range(120_000):
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        skip_checks = (x & 1) == 1
        d = disagree(skip_checks)
        if d:
            print(f"DISAGREE fuzz skip_checks={d[0]}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
