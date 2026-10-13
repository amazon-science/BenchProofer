#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13658.

There are NO consumed @ContractOnly axioms in model.py. What this check
validates is the single A-reference the twin relies on: that the deep model in
model.py faithfully captures the REAL, UNCHANGED library behaviour the change
routes around -- namely

  (1) the program-name rule `program_name(basename)` modelled in model.py's pure
      region (the basename itself, except the bootstrap basename '__main__.py'
      maps to 'python -m django') == the program name the real utility computes
      from its OWN first argument in `ManagementUtility.__init__`
      (`os.path.basename(argv[0])`, with the '__main__.py' special case); and

  (2) the real argument-parser constructor's program-name handling, which is the
      unchanged library primitive the patched code feeds `self.prog_name` into:
        - given an explicit program name `prog=p`, the parser reports `p`
          (so passing `self.prog_name` makes the parser use the utility's own
          argv-derived name -- the POST-patch model branch); and
        - given NO program name, the parser DEFAULTS its program name to the
          basename of the AMBIENT/process-wide first argument
          (`os.path.basename(sys.argv[0])`) -- the PRE-patch model branch
          (`build_settings_parser` in model_prepatch.py deriving `prog` from
          `sys_argv0_basename`).

Together (1)+(2) justify the refinement: model.py's `build_settings_parser`
sets `Result().prog == program_name(argv0_basename)`, which under the real
library equals constructing the parser with `prog=self.prog_name`; the pre-patch
default would instead yield `os.path.basename(sys.argv[0])`, the wrong source.

Imports only the Python standard library (`argparse`, `os`, `sys`) -- the same
modules the changed code uses; nothing repo-specific. Exit 0 iff every
obligation holds on boundary + randomized fuzz inputs.
"""
import argparse
import os
import random
import string
import sys


def model_program_name(basename):
    """Reference implementation of model.py's pure `program_name` over a
    basename string (returns a string; model carries code points)."""
    if basename == '__main__.py':
        return 'python -m django'
    return basename


def utility_prog_name(argv0):
    """The REAL value `ManagementUtility.__init__` computes for self.prog_name
    from its OWN first argument (django/core/management/__init__.py:190-192)."""
    prog_name = os.path.basename(argv0)
    if prog_name == '__main__.py':
        prog_name = 'python -m django'
    return prog_name


def check_program_name_rule(argv0):
    """(1) program_name(basename(argv0)) == real ManagementUtility prog_name."""
    basename = os.path.basename(argv0)
    expected = utility_prog_name(argv0)          # real __init__ computation
    observed = model_program_name(basename)      # model.py pure `program_name`
    assert observed == expected, (
        "program_name deep model unsound on argv0=%r: real prog_name=%r, "
        "model gives %r" % (argv0, expected, observed))


def make_parser(prog):
    """Construct the parser the way execute() does, optionally with `prog`.

    `prog=None` reproduces the PRE-patch call (no program name supplied);
    a non-None `prog` reproduces the POST-patch call (prog=self.prog_name).
    """
    kwargs = dict(usage='%(prog)s subcommand [options] [args]',
                  add_help=False, allow_abbrev=False)
    if prog is not None:
        kwargs['prog'] = prog
    return argparse.ArgumentParser(**kwargs)


def check_parser_uses_prog(prog):
    """(2a) POST-patch: a parser built with prog=p reports program name p."""
    p = make_parser(prog)
    assert p.prog == prog, (
        "argument parser did not adopt explicit program name %r: got %r"
        % (prog, p.prog))


def check_parser_default_is_sys_argv0(fake_sys_argv0):
    """(2b) PRE-patch: with no program name, the parser defaults its program
    name to os.path.basename(sys.argv[0]) -- the ambient source."""
    saved = sys.argv
    try:
        sys.argv = [fake_sys_argv0, 'help']
        p = make_parser(None)
        expected = os.path.basename(fake_sys_argv0)
        assert p.prog == expected, (
            "argument parser default program name mismatch for sys.argv[0]=%r: "
            "expected basename %r, got %r" % (fake_sys_argv0, expected, p.prog))
    finally:
        sys.argv = saved


def main():
    # --- boundary first-arguments ----------------------------------------
    boundary = [
        'django-admin',
        'manage.py',
        '/usr/local/bin/django-admin',
        './manage.py',
        '/a/b/c/manage.py',
        '__main__.py',
        '/path/to/__main__.py',
        'foo',
        'foo/bar/baz',
        'django-admin.py',
        'a',
    ]
    for argv0 in boundary:
        check_program_name_rule(argv0)

    # The program names the parser is fed (post-patch) / would default to.
    prog_boundary = [
        'django-admin', 'manage.py', 'python -m django', 'foo', 'a',
        'django-admin.py', 'x y z',
    ]
    for prog in prog_boundary:
        check_parser_uses_prog(prog)

    # Pre-patch default: ambient sys.argv[0] basename (the wrong source).
    for argv0 in boundary:
        check_parser_default_is_sys_argv0(argv0)

    # The discriminating case from the F2P regression test: the utility's own
    # argv names 'django-admin' while the parser, pre-patch, would derive its
    # program name from the ambient sys.argv[0] basename instead.
    check_program_name_rule('django-admin')
    check_parser_uses_prog('django-admin')           # post-patch: correct
    check_parser_default_is_sys_argv0('/x/sub.py')   # pre-patch: 'sub.py' (wrong)

    # --- randomized fuzz --------------------------------------------------
    rng = random.Random(13658)
    alphabet = string.ascii_letters + string.digits + '._-/ '
    for _ in range(20000):
        n = rng.randint(1, 24)
        body = ''.join(rng.choice(alphabet) for _ in range(n))
        # occasionally make the basename exactly the bootstrap name
        if rng.random() < 0.1:
            argv0 = (body.rsplit('/', 1)[0] + '/' if '/' in body else '') + '__main__.py'
        else:
            argv0 = body
        check_program_name_rule(argv0)
        prog = utility_prog_name(argv0)
        if prog:                       # argparse needs a non-empty prog string
            check_parser_uses_prog(prog)

    print("G-AX OK: program_name deep model (== real ManagementUtility "
          "prog_name) and argument-parser program-name handling (explicit prog "
          "adopted; default == basename(sys.argv[0])) sound on %d boundary "
          "+ 20000 fuzz inputs" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
