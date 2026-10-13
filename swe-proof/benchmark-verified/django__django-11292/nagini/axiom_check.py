#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11292.

This bundle consumes NO @ContractOnly axioms: the parser-exposure decision and
the run/skip gating are pure boolean logic, modelled deeply in model.py. The
deep model rests on two semantic facts about the standard-library argument
parser the gold patch uses (`argparse`, exactly as Django's CommandParser
subclasses it). This script validates those facts against the REAL `argparse`,
so the deep model's encoding is sound (the A-reference check of G-AX):

  (R1) "skip request offered iff validation required" -- model `parser_offers_skip`.
       The skip option is registered on the parser *exactly when* the command
       requires validation (the gold `create_parser` guards
       `parser.add_argument('--skip-checks', action='store_true', ...)` with
       `if self.requires_system_checks:`). We model the parser as registering
       the option iff `requires_validation`, and check that a parser built that
       way (a) exposes `skip_checks` in its parsed namespace exactly when the
       option was registered, and (b) rejects the `--skip-checks` token when it
       was not registered (so a request to a non-validating command has no
       effect / is not silently honoured by accident).

  (R2) "store_true default + presence" -- model `effective_skip` and the gate.
       For an `action='store_true'` option, the parsed namespace ALWAYS carries
       the attribute once the option is registered: False when the token is
       absent, True when present. This is why the gold `execute` can switch from
       `options.get('skip_checks')` to `options['skip_checks']` (the key is now
       always present) and why `will_run_validation`'s boolean algebra
       (`requires_validation and not (offered and requested_skip)`) is exact.

The end-to-end decision modelled by `will_run_validation` is then reproduced
against the real parsed namespace + the real gating expression
`requires_system_checks and not options['skip_checks']`, over the full boolean
cross-product of (requires_validation, token-present), and asserted equal to the
model's `will_run_validation`. Imports only the standard library `argparse`
(the very module the gold patch builds on). Exit 0 iff every obligation holds.
"""
import argparse
import sys


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def model_parser_offers_skip(requires_validation):
    # model.py `parser_offers_skip` post: Result() == requires_validation
    return requires_validation


def model_effective_skip(requires_validation, requested_skip):
    # model.py `effective_skip`
    if model_parser_offers_skip(requires_validation):
        return requested_skip
    return False


def model_will_run_validation(requires_validation, requested_skip):
    # model.py `will_run_validation` post:
    #   Result() == (requires_validation and not effective_skip(...))
    return requires_validation and not model_effective_skip(requires_validation, requested_skip)


# --- the real callee: an argparse parser built exactly as the gold patch ------

def build_real_parser(requires_validation):
    """Mirror the gold `create_parser` skip-option hunk on a real argparse
    parser: register `--skip-checks` (store_true) iff validation is required."""
    parser = argparse.ArgumentParser(prog="cmd")
    # the common store_true flags the command parser always has (representative)
    parser.add_argument('--traceback', action='store_true')
    parser.add_argument('--no-color', action='store_true')
    parser.add_argument('--force-color', action='store_true')
    if requires_validation:                       # gold: if self.requires_system_checks
        parser.add_argument('--skip-checks', action='store_true', help='Skip system checks.')
    return parser


def real_run_validation(requires_validation, pass_token):
    """The real end-to-end decision: parse the argv (with/without the
    --skip-checks token) and apply the gold gating expression
    `requires_system_checks and not options['skip_checks']`. Returns
    (parsed_ok, decision_or_None). parsed_ok is False if argparse rejected the
    token (e.g. the option was never registered)."""
    parser = build_real_parser(requires_validation)
    argv = ['--skip-checks'] if pass_token else []
    import io
    import contextlib
    try:
        # swallow argparse's stderr/SystemExit on an unrecognized token
        with contextlib.redirect_stderr(io.StringIO()):
            ns = parser.parse_args(argv)
    except SystemExit:
        return (False, None)
    options = vars(ns)
    # gold execute(): `if self.requires_system_checks and not options['skip_checks']`
    if requires_validation:
        # post-patch the key is always present for a validating command
        assert 'skip_checks' in options, (
            "store_true option not present in namespace for a validating command: %r" % options)
        decision = requires_validation and not options['skip_checks']
    else:
        # a non-validating command never registers the option and never checks
        decision = False
    return (True, decision)


def main():
    failures = 0

    # (R1)+(R2): the skip option is present in the namespace iff registered, and
    # a store_true option defaults to False when its token is absent.
    for requires_validation in (True, False):
        parser = build_real_parser(requires_validation)
        ns = vars(parser.parse_args([]))
        present = 'skip_checks' in ns
        assert present == model_parser_offers_skip(requires_validation), (
            "parser_offers_skip unsound: requires_validation=%r, namespace-present=%r, model=%r"
            % (requires_validation, present, model_parser_offers_skip(requires_validation)))
        if present:
            assert ns['skip_checks'] is False, (
                "store_true default not False with token absent: %r" % ns['skip_checks'])

    # a non-validating command must NOT accept the --skip-checks token (the
    # option is not offered): argparse rejects it -> SystemExit -> parsed_ok False
    ok, _ = real_run_validation(requires_validation=False, pass_token=True)
    assert ok is False, "non-validating command unexpectedly accepted --skip-checks"

    # end-to-end: the real decision == the model's will_run_validation over the
    # full boolean cross-product of (requires_validation, token-present), for the
    # cases the parser accepts (requested_skip only meaningful when offered).
    cases = [
        # requires_validation, requested_skip(token present)
        (True,  False),   # validating command, no skip token -> validation runs
        (True,  True),    # validating command, skip token    -> validation skipped (the fix)
        (False, False),   # non-validating command            -> never runs
    ]
    for requires_validation, requested_skip in cases:
        ok, decision = real_run_validation(requires_validation, requested_skip)
        assert ok, "argparse rejected an accepted-case argv: rv=%r skip=%r" % (
            requires_validation, requested_skip)
        expected = model_will_run_validation(requires_validation, requested_skip)
        if decision != expected:
            failures += 1
            print("MISMATCH rv=%r skip=%r: real=%r model=%r" % (
                requires_validation, requested_skip, decision, expected))

    if failures:
        print("G-AX FAIL: %d mismatch(es)" % failures)
        return 1
    print("G-AX OK: argparse store_true exposure/default semantics + the gating "
          "expression match the deep model over the boolean cross-product "
          "(skip-request honoured iff offered; validating command + token -> "
          "validation skipped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
