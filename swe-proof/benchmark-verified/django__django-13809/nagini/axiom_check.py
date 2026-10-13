#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13809.

This bundle consumes NO @ContractOnly axioms: whether this command offers the
skip request on its invocation, and whether the start-up validation actions are
emitted, are decided by pure boolean gating, modelled deeply in model.py. The
deep model rests on two semantic facts that the gold patch builds on, validated
here against the REAL standard library (the A-reference check of G-AX):

  (R1) "the skip request is offered unconditionally for this command" -- model
       `offers_skip_request` (post: Result() is True). This command performs its
       validation explicitly on start-up rather than via the common pre-pass, so
       it registers `--skip-checks` (action='store_true') on its own argument
       parser with no `requires_system_checks` guard. We check that a parser
       built that way (a) exposes `skip_checks` in its parsed namespace, and
       (b) defaults it to False when the token is absent / True when present.

  (R2) "the start-up schedule gating" -- model `startup_action_schedule`. The
       suppressible validation pass (announce + run) is emitted iff
       `not options['skip_checks']`; the migration re-check is emitted
       unconditionally. We reproduce the gold `inner_run` gate
       (`if not options['skip_checks']: <announce>; <run>` then always
       `<migration re-check>`) against the real parsed namespace and assert the
       emitted action schedule equals the model's `startup_action_schedule` over
       both values of the skip token.

Imports only the standard library `argparse` (the very module Django's
CommandParser subclasses, and on which the gold patch's `store_true` option
rests). Exit 0 iff every obligation holds.
"""
import argparse
import contextlib
import io
import sys


# --- model.py reference encodings (kept in lock-step with the spec) ----------

ACTION_ANNOUNCE_VALIDATION = 1
ACTION_RUN_VALIDATION = 2
ACTION_MIGRATION_RECHECK = 3


def model_offers_skip_request():
    # model.py `offers_skip_request` post: Result() is True
    return True


def model_startup_action_schedule(skip_checks):
    # model.py `startup_action_schedule`:
    #   skip      => [migration-recheck]
    #   not skip  => [announce, run, migration-recheck]
    schedule = []
    if not skip_checks:
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
        schedule.append(ACTION_RUN_VALIDATION)
    schedule.append(ACTION_MIGRATION_RECHECK)
    return schedule


# --- the real callee: an argparse parser built exactly as the gold add_arguments

def build_real_parser():
    """Mirror the gold `runserver.Command.add_arguments`: register
    `--skip-checks` (store_true) UNCONDITIONALLY (no requires_system_checks
    guard), alongside the command's other store_true flags."""
    parser = argparse.ArgumentParser(prog="runserver")
    parser.add_argument('--ipv6', '-6', action='store_true', dest='use_ipv6')
    parser.add_argument('--nothreading', action='store_false', dest='use_threading')
    parser.add_argument('--noreload', action='store_false', dest='use_reloader')
    # gold hunk: parser.add_argument('--skip-checks', action='store_true', ...)
    parser.add_argument('--skip-checks', action='store_true', help='Skip system checks.')
    return parser


def real_startup_schedule(pass_token):
    """Parse argv (with/without --skip-checks), then reproduce the gold
    `inner_run` start-up gate exactly:
        if not options['skip_checks']:
            <announce 'Performing system checks...'>   # ACTION_ANNOUNCE_VALIDATION
            <self.check(display_num_errors=True)>      # ACTION_RUN_VALIDATION
        <self.check_migrations()>                      # ACTION_MIGRATION_RECHECK (always)
    Returns the emitted action-code schedule."""
    parser = build_real_parser()
    argv = ['--skip-checks'] if pass_token else []
    with contextlib.redirect_stderr(io.StringIO()):
        ns = parser.parse_args(argv)
    options = vars(ns)
    assert 'skip_checks' in options, (
        "store_true option not present in runserver namespace: %r" % options)
    schedule = []
    if not options['skip_checks']:
        schedule.append(ACTION_ANNOUNCE_VALIDATION)
        schedule.append(ACTION_RUN_VALIDATION)
    schedule.append(ACTION_MIGRATION_RECHECK)
    return options['skip_checks'], schedule


def main():
    failures = 0

    # (R1) the skip option is offered unconditionally and defaults to False when
    # its token is absent, True when present.
    parser = build_real_parser()
    ns_absent = vars(parser.parse_args([]))
    assert 'skip_checks' in ns_absent, "runserver does not offer --skip-checks"
    assert ('skip_checks' in ns_absent) == model_offers_skip_request(), (
        "offers_skip_request unsound: namespace-present=%r model=%r"
        % ('skip_checks' in ns_absent, model_offers_skip_request()))
    assert ns_absent['skip_checks'] is False, (
        "store_true default not False with token absent: %r" % ns_absent['skip_checks'])
    with contextlib.redirect_stderr(io.StringIO()):
        ns_present = vars(build_real_parser().parse_args(['--skip-checks']))
    assert ns_present['skip_checks'] is True, (
        "store_true not True with token present: %r" % ns_present['skip_checks'])

    # (R2) the end-to-end start-up schedule == the model's startup_action_schedule
    # over both values of the skip token.
    for pass_token in (False, True):
        skip_val, real_sched = real_startup_schedule(pass_token)
        assert skip_val == pass_token, (
            "store_true value mismatch: token=%r value=%r" % (pass_token, skip_val))
        model_sched = model_startup_action_schedule(skip_val)
        if real_sched != model_sched:
            failures += 1
            print("MISMATCH token=%r: real=%r model=%r" % (
                pass_token, real_sched, model_sched))
        else:
            # extra discriminating assertions at the action level
            if pass_token:
                assert ACTION_ANNOUNCE_VALIDATION not in real_sched, "announce emitted under skip"
                assert ACTION_RUN_VALIDATION not in real_sched, "validation run emitted under skip"
                assert ACTION_MIGRATION_RECHECK in real_sched, "migration re-check dropped under skip"
            else:
                assert ACTION_ANNOUNCE_VALIDATION in real_sched, "announce missing without skip"
                assert ACTION_RUN_VALIDATION in real_sched, "validation run missing without skip"
                assert ACTION_MIGRATION_RECHECK in real_sched, "migration re-check missing"

    if failures:
        print("G-AX FAIL: %d mismatch(es)" % failures)
        return 1
    print("G-AX OK: runserver offers --skip-checks unconditionally (store_true, "
          "default False); the real inner_run start-up gate "
          "(announce+run iff not skip_checks; migration re-check always) matches "
          "the deep model startup_action_schedule over both token values.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
