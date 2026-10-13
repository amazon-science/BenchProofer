#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11292.

Refutes the R/I refinement legs of the two methods modeled in Solution.lean:

  * `registeredCommandOptions` — a command that performs project validation gains
    the `--skip-checks` opt-out option among the command-line options it
    recognises; a command that performs no validation does not.
  * `shouldRunSystemChecks` — project validation runs exactly when the command
    performs validation AND the user has not requested to skip it.

There are NO axioms in this bundle: every modeled op is pure boolean / list-frame
logic over free inputs, so the whole impl region is R/I-tagged (conf_skip=false).

ORACLE CHOICE.
  * Registration leg: the patched code does
        if self.requires_system_checks:
            parser.add_argument('--skip-checks', action='store_true', ...)
    on a real `argparse.ArgumentParser`. We build a REAL argparse parser the same
    way (seeded with a random frame of pre-existing options = `commonOptions`),
    conditionally add the flag exactly as the patch does, then ask the real
    parser whether it ACCEPTS `--skip-checks` (membership in the recognised set —
    the bijection of mapping.md §2). This grounds the R-leg in genuine argparse
    acceptance behaviour, not a re-implementation of it.
  * Gate leg: the patched `execute` gate is the boolean
        requires_system_checks and not options['skip_checks']
    transliterated verbatim. (The unchanged `self.check()` side effect is modeled
    as the decision bit "checks run"; mapping.md §2.)

  The SHADOW is Solution.lean transliterated (the registeredCommandOptions
  ensures-equations + the bool gate).
  We differential-test SHADOW vs ORACLE over the exhaustive 2-bit cube
  (requires_system_checks, skip_requested) x fuzzed option frames, >=10^5 inputs.
  Exit 0 iff zero disagreements. stdlib only.
"""
import argparse
import random
import string
import sys

SEED = 11292
N_FUZZ = 100_000
SKIP = "--skip-checks"

# The framework long-options every BaseCommand parser already carries at
# base_commit (create_parser, before the patched insertion) — the fixed part of
# the `commonOptions` frame. add_arguments may add more; we fuzz extras on top.
BASE_FRAME = [
    "--version", "--verbosity", "--settings", "--pythonpath",
    "--traceback", "--no-color", "--force-color",
]


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def shadow_registered(requires_system_checks, common_options):
    """`registeredCommandOptions` post-image (the ensures equations): append the
    opt-out flag iff the command validates."""
    if requires_system_checks:
        return list(common_options) + [SKIP]
    return list(common_options)


def shadow_should_run(requires_system_checks, skip_requested):
    """`shouldRunSystemChecks` post-image."""
    return bool(requires_system_checks and (not skip_requested))


# ---- ORACLE: real argparse (registration) + patched gate ------------------

def oracle_accepts_skip(requires_system_checks, common_options):
    """Build a real argparse parser the way patched create_parser does, then ask
    whether it ACCEPTS the --skip-checks option. Returns True iff accepted."""
    parser = argparse.ArgumentParser(prog="cmd", add_help=False,
                                     allow_abbrev=False)
    for opt in common_options:
        # store_true mirrors the flags; value-taking ones are irrelevant to
        # membership. Use store_true uniformly (acceptance is what matters).
        parser.add_argument(opt, action="store_true")
    # --- the patched hunk, verbatim shape ---
    if requires_system_checks:
        parser.add_argument(SKIP, action="store_true", help="Skip system checks.")
    # Probe acceptance: a recognised store_true option parses with no error;
    # an unrecognised one raises SystemExit (argparse error).
    try:
        ns = parser.parse_args([SKIP])
    except SystemExit:
        return False
    return getattr(ns, "skip_checks", False) is True


def oracle_should_run(requires_system_checks, skip_requested):
    """Patched execute gate, verbatim:
        if self.requires_system_checks and not options['skip_checks']:
            self.check()"""
    options = {"skip_checks": skip_requested}
    return bool(requires_system_checks and not options["skip_checks"])


def rand_frame(rng):
    """A random pre-existing option frame disjoint from --skip-checks (the
    `require skipChecksFlag ∉ commonOptions` precondition)."""
    n = rng.randint(0, 6)
    frame = list(BASE_FRAME) if rng.random() < 0.5 else []
    for _ in range(n):
        name = "--" + "".join(rng.choice(string.ascii_lowercase)
                              for _ in range(rng.randint(2, 8)))
        if name != SKIP and name not in frame:
            frame.append(name)
    return frame


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Exhaustive 2-bit cube on the booleans, with a representative frame, run
    # first; then fuzz frames for both bool settings.
    cube = [(r, s) for r in (False, True) for s in (False, True)]

    def check(requires, skip, frame):
        nonlocal count
        count += 1
        # Registration leg: SKIP in shadow set  <->  real parser accepts SKIP.
        sh_set = shadow_registered(requires, frame)
        sh_member = SKIP in sh_set
        orc_member = oracle_accepts_skip(requires, frame)
        if sh_member != orc_member:
            disagreements.append(("register", requires, skip, frame,
                                  sh_member, orc_member))
        # Frame preservation: every pre-existing option survives.
        if not all(o in sh_set for o in frame):
            disagreements.append(("frame", requires, skip, frame, sh_set, None))
        # Gate leg.
        sh_run = shadow_should_run(requires, skip)
        orc_run = oracle_should_run(requires, skip)
        if sh_run != orc_run:
            disagreements.append(("gate", requires, skip, frame, sh_run, orc_run))

    for requires, skip in cube:
        check(requires, skip, BASE_FRAME)
        if disagreements:
            break

    while count < N_FUZZ and not disagreements:
        frame = rand_frame(rng)
        requires = rng.random() < 0.5
        skip = rng.random() < 0.5
        check(requires, skip, frame)

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements[:8]))
        return 1
    print("G-CONF OK: R/I shadow of registeredCommandOptions + shouldRunSystemChecks "
          "agrees with real argparse acceptance + the patched execute gate on %d "
          "inputs (4 exhaustive cube + fuzzed option frames, seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
