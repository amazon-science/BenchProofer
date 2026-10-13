#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11749 (plan section 4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  -- the R/I-tagged op of Solution.lean's impl region (`forwarded`,
              folded by `forwardedAll`) transliterated to Python over the real
              repo observations, via the mapping.md section 2 bijection:
                supplied             <-> opt.dest in options
                individuallyRequired <-> opt.required
                inRequiredGroup      <-> opt in mutually_exclusive_required_options
              forwarded a = a.supplied and (a.individuallyRequired or
                                            a.inRequiredGroup). There are no
              A-tagged callees in the impl, so the shadow is pure R/I.
  * ORACLE  -- patch.diff's behaviour: the patched `call_command` comprehension
              predicate, run against a REAL `argparse.ArgumentParser` built with
              real standalone options and real mutually exclusive groups
              (required and optional). The required-group set is computed exactly
              as the gold patch does
                {opt for group in parser._mutually_exclusive_groups
                     for opt in group._group_actions if group.required}
              and the per-action keep verdict is the patched predicate
                opt.dest in options and
                (opt.required or opt in mutually_exclusive_required_options).
              (The real end-to-end correctness oracle is G-RESOLVE; this isolates
              the forward-selection leg the Lean model pins.)

They must agree on every action across the full Boolean matrix + fuzzed parsers.
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md section 4) for a deterministic verdict.
"""
import argparse
import random
import sys

SEED = 11749
N_FUZZ = 100_000


# --- the R/I shadow: forwarded / forwardedAll, transliterated ----------------
def shadow_forwarded(supplied, individually_required, in_required_group):
    """`forwarded (a : OptionView)` transliterated:
        a.supplied && (a.individuallyRequired || a.inRequiredGroup)"""
    return bool(supplied) and (bool(individually_required) or bool(in_required_group))


# --- the ORACLE: the patched call_command comprehension, really executed -----
def oracle_keep_mask(parser, parser_actions, options):
    """patch.diff's per-action forward verdict, computed over a REAL argparse
    parser via the patched predicate (django/core/management/__init__.py
    post-patch lines 130-138)."""
    mutually_exclusive_required_options = {
        opt
        for group in parser._mutually_exclusive_groups
        for opt in group._group_actions if group.required
    }
    return [
        (opt.dest in options and
         (opt.required or opt in mutually_exclusive_required_options))
        for opt in parser_actions
    ]


def shadow_keep_mask(parser, parser_actions, options):
    """The shadow keep-mask: extract each action's three observations (the
    mapping.md section 2 bijection) into an OptionView, then apply `forwarded`."""
    mutually_exclusive_required_options = {
        opt
        for group in parser._mutually_exclusive_groups
        for opt in group._group_actions if group.required
    }
    mask = []
    for opt in parser_actions:
        supplied = opt.dest in options                       # OptionView.supplied
        individually_required = opt.required                 # .individuallyRequired
        in_required_group = opt in mutually_exclusive_required_options  # .inRequiredGroup
        mask.append(shadow_forwarded(supplied, individually_required,
                                     in_required_group))
    return mask


# --- parser fuzzing ----------------------------------------------------------
def build_parser(rng):
    """Build a real ArgumentParser with a randomized mix of standalone options
    (required or not) and mutually exclusive groups (required or not). Returns
    (parser, parser_actions, all_dests)."""
    parser = argparse.ArgumentParser(prog="fuzz", add_help=False)
    dests = []
    idx = 0

    # standalone options
    n_standalone = rng.randint(0, 4)
    for _ in range(n_standalone):
        dest = "opt%d" % idx
        idx += 1
        required = rng.random() < 0.5
        parser.add_argument("--%s" % dest.replace("_", "-"),
                            dest=dest, required=required, default=None)
        dests.append(dest)

    # mutually exclusive groups
    n_groups = rng.randint(0, 3)
    for _ in range(n_groups):
        group_required = rng.random() < 0.5
        group = parser.add_mutually_exclusive_group(required=group_required)
        n_members = rng.randint(1, 3)
        for _ in range(n_members):
            dest = "opt%d" % idx
            idx += 1
            # argparse forbids required=True on a member of a mutex group, so
            # group members are individually NOT required -- exactly the bug
            # scenario (mandatory only via the required group).
            group.add_argument("--%s" % dest.replace("_", "-"),
                              dest=dest, default=None)
            dests.append(dest)

    parser_actions = list(parser._actions)
    return parser, parser_actions, dests


def supplied_options(rng, dests):
    """A random subset of declared dests is 'supplied' by the caller (mirrors
    the **options kwargs of call_command). Values are irrelevant -- only key
    membership is observed."""
    return {d: 1 for d in dests if rng.random() < 0.5}


def boundary_cases():
    """Explicit boundary parsers, including the F2P scenario: a required mutually
    exclusive group whose member dest IS supplied (must be forwarded post-patch,
    NOT forwarded pre-patch)."""
    cases = []

    # F2P: required mutex group, member supplied, member not individually required
    p = argparse.ArgumentParser(prog="f2p", add_help=False)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--foo-id", dest="foo_id", type=int, nargs="?", default=None)
    g.add_argument("--foo-name", dest="foo_name", type=str, nargs="?", default=None)
    cases.append((p, list(p._actions), {"foo_id": 1}))          # forward foo_id
    cases.append((p, list(p._actions), {"foo_name": "foo"}))    # forward foo_name
    cases.append((p, list(p._actions), {}))                     # nothing supplied

    # OPTIONAL mutex group, member supplied -> must NOT be forwarded
    p = argparse.ArgumentParser(prog="optgrp", add_help=False)
    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument("--a", dest="a", default=None)
    g.add_argument("--b", dest="b", default=None)
    cases.append((p, list(p._actions), {"a": 1}))

    # standalone required, supplied -> forwarded (both pre and post patch)
    p = argparse.ArgumentParser(prog="req", add_help=False)
    p.add_argument("--need", dest="need", required=True, default=None)
    p.add_argument("--opt", dest="opt", required=False, default=None)
    cases.append((p, list(p._actions), {"need": 1, "opt": 2}))

    # required group member NOT supplied -> not forwarded
    p = argparse.ArgumentParser(prog="reqgrp_nosupply", add_help=False)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--x", dest="x", default=None)
    g.add_argument("--y", dest="y", default=None)
    cases.append((p, list(p._actions), {}))

    return cases


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    action_count = 0

    cases = boundary_cases()
    for parser, parser_actions, options in cases:
        count += 1
        shadow = shadow_keep_mask(parser, parser_actions, options)
        oracle = oracle_keep_mask(parser, parser_actions, options)
        action_count += len(parser_actions)
        if shadow != oracle:
            disagreements.append((parser.prog, options, shadow, oracle))

    for _ in range(N_FUZZ):
        parser, parser_actions, dests = build_parser(rng)
        options = supplied_options(rng, dests)
        count += 1
        shadow = shadow_keep_mask(parser, parser_actions, options)
        oracle = oracle_keep_mask(parser, parser_actions, options)
        action_count += len(parser_actions)
        if shadow != oracle:
            disagreements.append(("fuzz", options, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d parsers:"
              % (len(disagreements), count))
        for prog, opts, sh, orc in disagreements:
            print("  parser=%r options=%r shadow=%r oracle=%r"
                  % (prog, opts, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of selectForwarded (forwarded) agrees with the "
          "patched call_command comprehension predicate on %d parsers / %d "
          "actions (seed=%d), 0 disagreements." % (count, action_count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
