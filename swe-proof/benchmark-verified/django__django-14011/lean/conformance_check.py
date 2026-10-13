#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of the two implementations
(implementation_bindResources, implementation_releaseResources) against the
patch.diff behaviour over the connection registry.

The impl regions are all R/I (no A-tagged op), so this runs a real fuzz. The
shadows reproduce the Lean impls op-for-op:

  bindResources(reg, provided):
      r = list(reg)
      for c in provided: r = setRes(r, c)      # connections[alias] = conn
      return r
  releaseResources(reg):
      return [releaseRes(c) for c in reg]       # connection.close() for each

Each is diffed against an independent reconstruction of the POST-patch behaviour:
  - behavior 1: installing connections_override into the registry dict
    (connections[alias] = conn), then reading the registry back;
  - behavior 2: connections.close_all() marking every connection closed.

A "registry" is a list of (name, is_open) pairs with unique names; a "provided"
collection is likewise a list of (name, is_open) with unique names (mirrors a
dict's values, keyed by alias). stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14011          # pinned in mapping.md
N = 120_000           # >= 10^5

NAMES = ["default", "replica", "other", "analytics", "cache", "legacy", "ro", "rw"]


# ---- R/I shadows of the Lean impls ---------------------------------------

def set_res(reg, c):
    """setRes: replace entry with matching name in place, else append."""
    if any(d[0] == c[0] for d in reg):
        return [c if d[0] == c[0] else d for d in reg]
    return reg + [c]


def shadow_bind(reg, provided):
    r = list(reg)
    for c in provided:
        r = set_res(r, c)
    return r


def shadow_release(reg):
    return [(c[0], False) for c in reg]


# ---- independent reconstruction of POST-patch behaviour ------------------

def patched_bind(reg, provided):
    """process_request_thread: connections[alias] = conn for each provided.

    Modeled as a dict keyed by alias, seeded from reg, then overwritten by each
    provided connection; read back in registry order (existing keys keep their
    slot, new keys append) to match __setitem__/iteration semantics."""
    order = [name for name, _ in reg]
    d = {name: openp for name, openp in reg}
    for name, openp in provided:
        if name not in d:
            order.append(name)
        d[name] = openp
    return [(name, d[name]) for name in order]


def patched_release(reg):
    """close_all(): every connection in the registry is closed."""
    return [(name, False) for name, _ in reg]


# ---- fuzzers --------------------------------------------------------------

def rand_registry(rng):
    k = rng.randint(0, 5)
    names = rng.sample(NAMES, min(k, len(NAMES)))
    return [(n, rng.choice([True, False])) for n in names]


def rand_provided(rng):
    k = rng.randint(0, 4)
    names = rng.sample(NAMES, min(k, len(NAMES)))
    return [(n, rng.choice([True, False])) for n in names]


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases (incl. the F2P shape: one live conn closed).
    fixed_bind = [
        ([], []),
        ([("default", True)], []),
        ([], [("default", True)]),
        ([("default", False)], [("default", True)]),     # override replaces in place
        ([("default", True)], [("replica", True)]),       # new alias appends
        ([("default", True), ("replica", False)],
         [("default", False), ("other", True)]),
    ]
    fixed_release = [
        [],
        [("default", True)],                               # the F2P case: live -> closed
        [("default", True), ("replica", True)],
        [("default", False)],
        [("default", True), ("replica", False), ("other", True)],
    ]

    cases_bind = fixed_bind + [
        (rand_registry(rng), rand_provided(rng)) for _ in range(N // 2)
    ]
    cases_release = fixed_release + [
        rand_registry(rng) for _ in range(N // 2)
    ]

    for reg, provided in cases_bind:
        got = shadow_bind(reg, provided)
        want = patched_bind(reg, provided)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(("bind", (reg, provided), got, want))

    for reg in cases_release:
        got = shadow_release(reg)
        want = patched_release(reg)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(("release", reg, got, want))

    total = len(cases_bind) + len(cases_release)
    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for tag, inp, g, w in examples:
            print(f"  {tag} in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {total} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
