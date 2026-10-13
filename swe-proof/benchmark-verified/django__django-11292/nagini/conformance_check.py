#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11292 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (there are none inside the impl bodies; the Ensures live in the
elided post-condition regions). The @Pure helpers `skip_request_offered` and
`effective_skip` copy over as plain functions. No @ContractOnly callees exist
in this bundle. No PSeq is used (the carriers are plain bools), so no shim is
needed.

ORACLE: the REAL patched repo code per mapping.md section 1 —
`django.core.management.base.BaseCommand`, imported from /testbed after the
gate applies the gold patch. Two sensed observations:

  (1) parser_offers_skip <-> whether `create_parser` registers the
      `--skip-checks` option, observed as the presence of the `skip_checks`
      key in the namespace parsed from an empty argv (same observation the
      G-AX script uses against stdlib argparse).
  (2) will_run_validation <-> whether the validation pass actually runs,
      observed via a sensing subclass whose `check` records the call, driven
      through the real invocation path (create_parser -> parse_args ->
      execute) exactly as `run_from_argv` drives it.

Type bridge (mapping.md section 2): `requires_validation` is the command's
requires_system_checks flag (identity on bools); `requested_skip` is the
presence of the `--skip-checks` token on the invocation argv. For a command
that does not require validation the parser rejects the token (the parser
raises instead of parsing); the validation pass does not run on that path
either, so the model's False decision is compared against the sensed
"did not run" observation — the bridge mapping.md documents.

Input domain: the Requires regions are empty, so every point of the boolean
cross-product (requires_validation, requested_skip) is Requires-satisfying.
The domain is finite (4 points); the >=1e5 budget is spent as all 4 boundary
points plus 100000 fuzz draws over the same domain with a pinned seed, each
draw exercising the real code path end-to-end with a fresh command instance.
Pinned fuzz seed: 11292.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plus the /testbed package under test).
"""
import contextlib
import io
import json
import random
import sys

SEED = 11292
N_FUZZ = 100_000


# --- pure helpers from model.py, contracts stripped ---------------------------

def skip_request_offered(requires_validation):
    return requires_validation


def effective_skip(requires_validation, requested_skip):
    if skip_request_offered(requires_validation):
        return requested_skip
    return False


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def parser_offers_skip(requires_validation):
    if requires_validation:
        return True
    return False


def will_run_validation(requires_validation, requested_skip):
    skip = parser_offers_skip(requires_validation) and requested_skip
    if requires_validation and not skip:
        return True
    return False


# --- oracle: the real patched command base class from /testbed ----------------

def make_sensing_class():
    from django.core.management.base import BaseCommand

    class SensingCommand(BaseCommand):
        """Real BaseCommand whose validation pass records that it ran.
        Only the sensed observable is stubbed; the decision logic under test
        (option registration + the run/skip gate) is the real repo code."""

        def __init__(self, requires_validation, **kwargs):
            self.requires_system_checks = requires_validation
            self.check_ran = False
            super(SensingCommand, self).__init__(**kwargs)

        def check(self, *args, **kwargs):
            self.check_ran = True

        def handle(self, *args, **options):
            return None

    return SensingCommand


def real_parser_offers_skip(sensing_cls, requires_validation):
    cmd = sensing_cls(requires_validation)
    parser = cmd.create_parser('prog', 'cmd')
    ns = vars(parser.parse_args([]))
    return 'skip_checks' in ns


def real_will_run_validation(sensing_cls, requires_validation, requested_skip):
    """Drive the real invocation path the way run_from_argv does and return
    whether the validation pass ran. A rejected argv (token not accepted by
    the parser) means the command never proceeds: the pass did not run."""
    from django.core.management.base import CommandError
    cmd = sensing_cls(requires_validation,
                      stdout=io.StringIO(), stderr=io.StringIO())
    parser = cmd.create_parser('prog', 'cmd')
    argv = ['--skip-checks'] if requested_skip else []
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            options = parser.parse_args(argv)
    except (SystemExit, CommandError):
        return cmd.check_ran  # invocation rejected; the pass never ran
    cmd_options = vars(options)
    args = cmd_options.pop('args', ())
    cmd.execute(*args, **cmd_options)
    return cmd.check_ran


# --- differential loop ---------------------------------------------------------

def check_point(sensing_cls, requires_validation, requested_skip):
    """Compare shadow vs oracle on one input point; return error str or None."""
    shadow_offers = parser_offers_skip(requires_validation)
    real_offers = real_parser_offers_skip(sensing_cls, requires_validation)
    if shadow_offers != real_offers:
        return ("DISAGREEMENT parser_offers_skip\n"
                "  requires_validation=%r\n  shadow=%r\n  real=%r"
                % (requires_validation, shadow_offers, real_offers))

    shadow_runs = will_run_validation(requires_validation, requested_skip)
    real_runs = real_will_run_validation(
        sensing_cls, requires_validation, requested_skip)
    if shadow_runs != real_runs:
        return ("DISAGREEMENT will_run_validation\n"
                "  requires_validation=%r requested_skip=%r\n"
                "  shadow=%r\n  real=%r"
                % (requires_validation, requested_skip, shadow_runs, real_runs))
    return None


def main():
    sensing_cls = make_sensing_class()

    checked = 0
    boundary = [(True, False), (True, True), (False, False), (False, True)]
    for rv, rs in boundary:
        err = check_point(sensing_cls, rv, rs)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        rv = rng.random() < 0.5
        rs = rng.random() < 0.5
        err = check_point(sensing_cls, rv, rs)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real command behaviour on %d inputs "
          "(%d boundary + %d fuzz over the boolean cross-product, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
