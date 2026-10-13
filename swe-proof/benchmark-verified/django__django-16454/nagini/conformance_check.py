#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16454 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (the impl region itself contains no Requires/Ensures lines).
The three minimal model classes (OpeningParser / SubCommandBuilder /
SubCommandParser) are plain-Python shims of the model's classes with the same
fields and constructor defaults. There is no PSeq usage and no @Pure helper in
this bundle. The single @ContractOnly callee, `is_error_aware_kind`, calls the
REAL repo predicate: `issubclass(parser_class, CommandParser)` (the unchanged
guard, per mapping.md section 3.1) — the token is bridged to a concrete class
first (see the type bridge below).

ORACLE: the REAL patched repo code the model models per mapping.md —
`django.core.management.base.CommandParser.add_subparsers` (the changed
function, modeled by `open_subcommand_group`) followed by the unchanged stdlib
`argparse._SubParsersAction.add_parser` construction step (modeled by
`build_subcommand_parser`). The gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched module importable.
Observation points, exactly the modeling boundary of mapping.md section 2:

  * the sub-command builder's recorded construction policy is the
    `_parser_class` the returned action carries: a `functools.partial` binding
    `called_from_command_line` <-> (injects_flag=True, inherited_style=<bound
    value>); the bare requested class <-> injects_flag=False with no binding
    recorded;
  * a constructed sub-command parser's flag is `called_from_command_line` on
    the object `add_parser` returns: attribute present <-> carries_flag=True
    with error_style=<its value>; attribute absent <-> carries_flag=False.

Type bridge (mapping.md section 2): `error_style`/`inherited_style` are
`Optional[bool]` <-> the real flag's three observable settings (None / True /
False), compared with `is` identity (interned singletons, matching the spec's
`is`). `parser_class_token: int` is an opaque kind token; the bridge maps a
token to a concrete class via a fixed pool (token -> POOL[token % len(POOL)]),
a deterministic function of the token, so the axiom's determinism carries
over. The frame clauses of the plain path (prior field values kept verbatim)
are checked by seeding the shadow's builder/child fields with varied prior
values and asserting the real side recorded no binding / no attribute while
the shadow left the prior value in place.

Input domain (the model's Requires are permission-only, so every
(parent-flag, token, prior values) triple qualifies): boundary cases cover
every flag setting crossed with every pool class, the default-kind call (no
explicit class requested, which the real method resolves to the opening
parser's own kind), a subclass opening parser, and all prior-value seeds;
fuzz draws flags, tokens (large/negative ints included), prior seeds, and
parent kinds at random.

>= 1e5 Requires-satisfying inputs: boundary + 100000 fuzz cases.
Pinned fuzz seed: 16454.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import argparse
import functools
import random
import json
import sys

from django.core.management.base import CommandParser

SEED = 16454
N_FUZZ = 100_000

MISSING = object()  # sentinel: "the real child carries no flag attribute"


# --- shims of the model's minimal classes (contracts stripped) ---------------

class OpeningParser:
    def __init__(self):
        self.error_style = None


class SubCommandBuilder:
    def __init__(self):
        self.injects_flag = False
        self.inherited_style = None


class SubCommandParser:
    def __init__(self):
        self.carries_flag = False
        self.error_style = None


# --- the parser-class kind pool + the token bridge ----------------------------

class CmdSub(CommandParser):
    pass


class CmdSubSub(CmdSub):
    pass


class VanillaSub(argparse.ArgumentParser):
    pass


# error-aware kinds first, then plain kinds; the bridge is token -> pool index.
CLASS_POOL = [CommandParser, CmdSub, CmdSubSub,
              argparse.ArgumentParser, VanillaSub]


def token_to_class(parser_class_token):
    return CLASS_POOL[parser_class_token % len(CLASS_POOL)]


# --- @ContractOnly callee: the REAL repo predicate ----------------------------

def is_error_aware_kind(parser_class_token):
    # the real unchanged guard the modeled function calls (mapping.md 3.1)
    return issubclass(token_to_class(parser_class_token), CommandParser)


# --- the impl region of model.py, verbatim ------------------------------------

def open_subcommand_group(parent, builder, parser_class_token):
    if is_error_aware_kind(parser_class_token):
        builder.injects_flag = True
        builder.inherited_style = parent.error_style
    else:
        builder.injects_flag = False


def build_subcommand_parser(builder, child):
    if builder.injects_flag:
        child.carries_flag = True
        child.error_style = builder.inherited_style
    else:
        child.carries_flag = False


# --- oracle: the real patched method + the unchanged constructor --------------

def real_observe(parent_cls, parent_flag, requested_cls, default_kind):
    """Run the REAL patched add_subparsers on a fresh opening parser and the
    unchanged add_parser construction, and return the observables:
      (real_injects, real_inherited, real_carries, real_child_style)
    where real_inherited/real_child_style are MISSING when not recorded."""
    parent = parent_cls(prog="prog", add_help=False,
                        called_from_command_line=parent_flag)
    if default_kind:
        action = parent.add_subparsers()
    else:
        action = parent.add_subparsers(parser_class=requested_cls)

    # the recorded construction policy (mapping.md sec. 2: partial-binding
    # <-> injects_flag/inherited_style; bare class <-> no injection)
    factory = action._parser_class
    if isinstance(factory, functools.partial):
        real_injects = True
        real_inherited = factory.keywords.get("called_from_command_line",
                                              MISSING)
    else:
        real_injects = False
        real_inherited = MISSING
        # no binding recorded at all: the factory is the bare requested class
        expected_bare = parent_cls if default_kind else requested_cls
        if factory is not expected_bare:
            return None  # unexpected policy shape: itself a disagreement

    # the unchanged sub-command constructor (end-to-end observable)
    child = action.add_parser("sub", add_help=False)
    real_carries = hasattr(child, "called_from_command_line")
    real_child_style = getattr(child, "called_from_command_line", MISSING)
    return real_injects, real_inherited, real_carries, real_child_style


def check_case(parent_cls, parent_flag, token, default_kind,
               prior_builder_style, prior_child_style):
    # --- shadow ---------------------------------------------------------
    parent = OpeningParser()
    parent.error_style = parent_flag
    builder = SubCommandBuilder()
    builder.inherited_style = prior_builder_style
    child = SubCommandParser()
    child.error_style = prior_child_style

    open_subcommand_group(parent, builder, token)
    build_subcommand_parser(builder, child)

    # --- real -----------------------------------------------------------
    requested_cls = token_to_class(token)
    obs = real_observe(parent_cls, parent_flag, requested_cls, default_kind)

    def fail(why, real_repr):
        print("DISAGREEMENT (%s)\n"
              "  parent_cls=%r parent_flag=%r token=%r requested_cls=%r "
              "default_kind=%r\n"
              "  prior_builder_style=%r prior_child_style=%r\n"
              "  shadow: injects=%r inherited=%r carries=%r child_style=%r\n"
              "  real:   %s"
              % (why, parent_cls, parent_flag, token, requested_cls,
                 default_kind, prior_builder_style, prior_child_style,
                 builder.injects_flag, builder.inherited_style,
                 child.carries_flag, child.error_style, real_repr))
        return False

    if obs is None:
        return fail("policy shape", "factory neither partial nor the bare "
                                    "requested class")
    real_injects, real_inherited, real_carries, real_child_style = obs
    real_repr = ("injects=%r inherited=%r carries=%r child_style=%r"
                 % (real_injects, real_inherited, real_carries,
                    real_child_style))

    if builder.injects_flag != real_injects:
        return fail("injection decision", real_repr)
    if builder.injects_flag:
        if builder.inherited_style is not real_inherited:
            return fail("inherited value", real_repr)
    else:
        # frame: the shadow left the prior value; the real side recorded no
        # binding (checked in real_observe: the factory is the bare class)
        if builder.inherited_style is not prior_builder_style:
            return fail("plain-path builder frame", real_repr)

    if child.carries_flag != real_carries:
        return fail("child flag presence", real_repr)
    if child.carries_flag:
        if child.error_style is not real_child_style:
            return fail("child flag value", real_repr)
    else:
        if real_child_style is not MISSING:
            return fail("plain child unexpectedly carries a flag", real_repr)
        if child.error_style is not prior_child_style:
            return fail("plain-path child frame", real_repr)
    return True


FLAGS = (None, True, False)
PARENT_CLASSES = (CommandParser, CmdSub)


def boundary_cases():
    cases = []
    for parent_cls in PARENT_CLASSES:
        for parent_flag in FLAGS:
            # the default kind (no explicit class requested): the real method
            # resolves it to the opening parser's own kind, which is
            # error-aware; bridge the token to that same class.
            default_token = CLASS_POOL.index(parent_cls)
            cases.append((parent_cls, parent_flag, default_token, True,
                          None, None))
            # every pool kind, requested explicitly, with varied prior seeds
            for token in range(len(CLASS_POOL)):
                for prior_b in FLAGS:
                    for prior_c in FLAGS:
                        cases.append((parent_cls, parent_flag, token, False,
                                      prior_b, prior_c))
            # token bridge edges: negative and huge tokens
            for token in (-1, -5, 5, 10 ** 9, 2 ** 63):
                cases.append((parent_cls, parent_flag, token, False,
                              None, None))
    return cases


def fuzz_case(rng):
    parent_cls = PARENT_CLASSES[rng.randrange(len(PARENT_CLASSES))]
    parent_flag = FLAGS[rng.randrange(3)]
    prior_b = FLAGS[rng.randrange(3)]
    prior_c = FLAGS[rng.randrange(3)]
    r = rng.randrange(10)
    if r == 0:
        # the default-kind call; token bridged to the parent's own kind
        return (parent_cls, parent_flag, CLASS_POOL.index(parent_cls), True,
                prior_b, prior_c)
    if r <= 6:
        token = rng.randrange(len(CLASS_POOL))
    elif r <= 8:
        token = rng.randrange(-10 ** 6, 10 ** 6)
    else:
        token = rng.randrange(2 ** 62, 2 ** 64)
    return parent_cls, parent_flag, token, False, prior_b, prior_c


def main():
    checked = 0
    boundary = boundary_cases()
    for case in boundary:
        if not check_case(*case):
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        if not check_case(*fuzz_case(rng)):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched sub-command-group opening + "
          "unchanged sub-command construction on %d inputs (%d boundary + %d "
          "fuzz, seed %d)." % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
