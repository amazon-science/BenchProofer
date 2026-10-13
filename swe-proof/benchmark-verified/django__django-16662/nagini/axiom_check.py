#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16662.

There is no @ContractOnly axiom in model.py. The one out-of-text trust point is
the A-reference of refinement.md step A2: the deep ordering key `compkey`
(model.py, the linearised pair (group flag, module code)) must order import
lines identically to the REAL ordering performed by the gold patch, namely
CPython `sorted(iterable, key=lambda i: (i.split()[0] == "from", i.split()[1]))`.

This script executes the REAL callees (`sorted` + the gold key lambda, and
Python tuple comparison) on boundary + randomized-fuzz inputs and asserts:

  (A-reference, part 1) ascending integer order on `compkey(f, m)` is EXACTLY
      ascending order on the real pair key (bool(f), name) — the linearisation
      is order-preserving with the group flag dominating.

  (A-reference, part 2) running the real `sorted` with the real gold key on
      assembled import-line strings produces the grouped order the model's
      ascending-`compkey` arrangement encodes: every plain `import` line before
      every `from ... import` line, module-ordered within each group. In
      particular it reproduces the FAIL_TO_PASS observation
      `import datetime`, `import time`, `from django.db import migrations, models`.

  (control) the PRE-FIX key `lambda i: i.split()[1]` produces the REJECTED
      interleaved order on that same configuration (so the spec's discriminating
      clause is the real behavioural change).

Imports nothing repo-specific: `sorted`, tuple comparison and the gold key are
plain Python; the gold key lambda is reproduced verbatim from
django/db/migrations/writer.py:178. Exit 0 iff every obligation holds.
"""
import random
import sys

SCALE = 1000000000  # the model's group-flag scale (model.py compkey)


# --- model.py reference encoding (kept in lock-step with compkey) ------------

def compkey(is_from, module):
    """Reference of model.py's deep ordering key: the linearised pair."""
    return is_from * SCALE + module


# --- the REAL ordering the gold patch performs -------------------------------

def gold_key(i):
    """The gold patch's sort key VERBATIM (writer.py:178, post-patch)."""
    return (i.split()[0] == "from", i.split()[1])


def prefix_key(i):
    """The pre-fix sort key (writer.py:178, pre-patch): module name only."""
    return i.split()[1]


# --- checks ------------------------------------------------------------------

def check_linearisation_order(items):
    """Assert: for every ordered pair of distinct lines, ascending compkey order
    equals ascending real-tuple-key order. `items` is a list of
    (is_from, module_code, module_name) triples with module_code an
    order-preserving code of module_name (code_a < code_b iff name_a < name_b)."""
    for (f1, c1, n1) in items:
        for (f2, c2, n2) in items:
            real_lt = (bool(f1), n1) < (bool(f2), n2)
            model_lt = compkey(f1, c1) < compkey(f2, c2)
            assert real_lt == model_lt, (
                "linearisation unsound: real (%r,%r)<(%r,%r)=%r but "
                "compkey %d<%d=%r"
                % ((bool(f1), n1), (bool(f2), n2), real_lt,
                   compkey(f1, c1), compkey(f2, c2), model_lt))


def assert_grouped(sorted_lines):
    """Assert the sorted output groups all plain imports before all from-imports
    and is module-ordered within each group (the behaviour the model pins)."""
    seen_from = False
    prev_plain_mod = None
    prev_from_mod = None
    for line in sorted_lines:
        is_from = line.split()[0] == "from"
        mod = line.split()[1]
        if is_from:
            seen_from = True
            if prev_from_mod is not None:
                assert prev_from_mod <= mod, (
                    "from-group not module-ordered: %r then %r"
                    % (prev_from_mod, mod))
            prev_from_mod = mod
        else:
            assert not seen_from, (
                "a plain import follows a from-import: %r in %r"
                % (line, sorted_lines))
            if prev_plain_mod is not None:
                assert prev_plain_mod <= mod, (
                    "import-group not module-ordered: %r then %r"
                    % (prev_plain_mod, mod))
            prev_plain_mod = mod


def check_sorted_matches_model(lines):
    """Assert the real sorted(gold_key) order == ascending-compkey order, by
    comparing the real sorted output to the order the model encodes."""
    real = sorted(lines, key=gold_key)
    assert_grouped(real)
    # the model orders by compkey of (is_from, order-code(module)); build the
    # order-code from the distinct module names present (rank in sorted order).
    names = sorted({ln.split()[1] for ln in lines})
    rank = {nm: r for r, nm in enumerate(names)}
    model_order = sorted(
        lines, key=lambda i: compkey(1 if i.split()[0] == "from" else 0,
                                     rank[i.split()[1]]))
    assert real == model_order, (
        "real sorted(gold_key) %r != ascending-compkey model order %r"
        % (real, model_order))


def main():
    # --- A-reference part 1: linearisation order on boundary + fuzz ---------
    module_names = ["a", "datetime", "django", "django.conf", "django.db",
                    "time", "uuid", "z", "zoneinfo", "abc.def", "b", "bb"]
    module_names = sorted(set(module_names))
    code = {nm: r for r, nm in enumerate(module_names)}
    items = [(f, code[nm], nm) for f in (0, 1) for nm in module_names]
    check_linearisation_order(items)

    rng = random.Random(16662)
    for _ in range(2000):
        sample = rng.sample(module_names, rng.randint(1, len(module_names)))
        sample = sorted(set(sample))
        c = {nm: r for r, nm in enumerate(sample)}
        fuzz = [(rng.randint(0, 1), c[nm], nm) for nm in sample]
        check_linearisation_order(fuzz)

    # --- A-reference part 2: the real sorted(gold_key) == model order -------
    def imp(mod):
        return "import %s" % mod

    def frm(mod):
        return "from %s import x" % mod

    boundary_configs = [
        # the FAIL_TO_PASS configuration
        [imp("datetime"), imp("time"), frm("django.db")],
        # from-module sorts before a plain import module, yet must follow it
        [imp("time"), frm("django.db")],
        [imp("zoneinfo"), frm("abc")],
        # all from
        [frm("django.conf"), frm("django.db"), frm("abc")],
        # all plain
        [imp("uuid"), imp("datetime"), imp("time")],
        # mixed, multiple in each group
        [imp("time"), imp("datetime"), frm("django.db"), frm("django.conf"),
         imp("uuid")],
        # single line
        [imp("os")],
        [frm("sys")],
    ]
    for cfg in boundary_configs:
        check_sorted_matches_model(cfg)

    alphabet = module_names
    for _ in range(5000):
        n = rng.randint(1, 6)
        lines = []
        used = set()
        for _ in range(n):
            mod = rng.choice(alphabet)
            kind = rng.randint(0, 1)
            line = frm(mod) if kind else imp(mod)
            if line in used:
                continue
            used.add(line)
            lines.append(line)
        if lines:
            check_sorted_matches_model(lines)

    # --- control: the PRE-FIX key produces the REJECTED interleaving --------
    f2p = [imp("datetime"), imp("time"), frm("django.db")]
    prefix_order = sorted(f2p, key=prefix_key)
    # module-only sort interleaves: datetime, django.db, time
    assert prefix_order == [imp("datetime"), frm("django.db"), imp("time")], (
        "pre-fix key did not interleave as expected: %r" % prefix_order)
    # and it is NOT grouped (a plain import 'time' follows the from-import)
    interleaved_violation = False
    try:
        assert_grouped(prefix_order)
    except AssertionError:
        interleaved_violation = True
    assert interleaved_violation, (
        "pre-fix order unexpectedly satisfied the grouping the model requires")

    print("G-AX OK: compkey linearisation == real tuple key over %d boundary "
          "pairs + 2000 fuzz; real sorted(gold_key) == ascending-compkey model "
          "order over %d boundary + 5000 fuzz configs; pre-fix key rejected "
          "(interleaved) on the FAIL_TO_PASS configuration."
          % (len(items), len(boundary_configs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
