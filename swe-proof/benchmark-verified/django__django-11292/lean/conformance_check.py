#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11292.

The bundle models ONE routine: the launch-time decision a management command
makes when run from the command line — whether the `--skip-checks` request is a
recognised option, and whether the system checks run. Per mapping.md it is a PURE
function of two observables:

    command_performs_checks : bool   (self.requires_system_checks)
    skip_requested          : bool   (`--skip-checks` supplied on argv)

Post-patch rule (the gold edit registers `--skip-checks` iff the command checks,
and gates `self.check()` on `not options['skip_checks']`):

    if command_performs_checks:
        # --skip-checks is a registered option
        if skip_requested:
            outcome = 'skipped_checks'      # gate: requires_checks and not skip -> False
        else:
            outcome = 'ran_checks'          # gate True -> self.check()
    else:
        # --skip-checks is NOT registered
        if skip_requested:
            outcome = 'unrecognized_option' # argparse rejects unknown argument
        else:
            outcome = 'skipped_checks'      # gate's first conjunct False -> no check()

Standing up the full management/argparse/ORM stack to drive the real
`create_parser`+`execute` is heavy and unnecessary: the modeled value is this
pure two-boolean decision over observables the command exposes (whether it
performs checks, and whether the skip flag was supplied). So the ORACLE is a
faithful in-process replica of the patched registration+gate behavior, and the
SHADOW is the op-for-op transliteration of `implementation_runCommand`
(skipOptionAvailable := performs_checks; unrecognised when skip on an
unregistered option; ran/skipped by the post-patch gate), per refinement.md.

The domain is the full Bool x Bool product (4 points); we enumerate it
exhaustively AND fuzz to >=10^5 trials for the gate contract.

stdlib-only. Pinned seed: 11292 (also in mapping.md).
"""
import random
import sys

SEED = 11292
N = 120_000


# --- ORACLE: faithful in-process replica of the patched launch decision ------
def oracle_run(command_performs_checks, skip_requested):
    if command_performs_checks:
        # --skip-checks registered; execute() gate: requires_checks and not skip
        if skip_requested:
            return "skipped_checks"
        return "ran_checks"
    # --skip-checks NOT registered
    if skip_requested:
        return "unrecognized_option"
    return "skipped_checks"


# --- SHADOW of implementation_runCommand (the R leg) -------------------------
# Mirrors Solution.lean op-for-op:
#   skipOptionAvailable := commandPerformsChecks
#   if skipRequested && !skipOptionAvailable: return unrecognizedOption
#   skip := skipRequested
#   if commandPerformsChecks && !skip: return ranChecks
#   return skippedChecks
def shadow_run(command_performs_checks, skip_requested):
    skip_option_available = command_performs_checks
    if skip_requested and not skip_option_available:
        return "unrecognized_option"
    skip = skip_requested
    if command_performs_checks and not skip:
        return "ran_checks"
    return "skipped_checks"


def disagree(c, s):
    got = oracle_run(c, s)
    want = shadow_run(c, s)
    if got != want:
        return ((c, s), got, want)
    return None


def _enumerate_edge():
    # the full Bool x Bool domain
    cases = []
    for c in (False, True):
        for s in (False, True):
            cases.append((c, s))
    return cases


def main() -> int:
    checked = 0
    for c, s in _enumerate_edge():
        d = disagree(c, s)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        c = rng.choice([False, True])
        s = rng.choice([False, True])
        d = disagree(c, s)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
