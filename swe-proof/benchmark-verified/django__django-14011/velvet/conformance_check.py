#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14011 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW — the R/I-tagged ops of Solution.lean's impl regions, transliterated
             to Python over the real repo types via the mapping.md bijection:
               - installPreferred: the override-precedence merge
                 `preferred ++ registry` under first-match lookup;
               - releaseAll: map every connection state to closed (releasedSeq).
  * ORACLE — patch.diff's behaviour, realized by the REAL repo callees the
             patch invokes (the actual correctness oracle, G-RESOLVE):
               - install: real `BaseConnectionHandler.__setitem__`/`__getitem__`
                 layered over the pre-existing registry;
               - release: real `ConnectionHandler.close_all`.

There are no A-tagged ops *inside the computed output* (the only A legs are the
A-reference deep models, whose equality to these same real callees is exactly
what is being differentially tested), so the shadow is pure R/I.

They must agree on every input. Exit 0 iff zero disagreements. Runs in-container;
stdlib only. Fuzz seed pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
import types

SEED = 14011
N_FUZZ = 100_000


# ---------- SHADOW: transliterated R/I do-blocks ---------------------------

def shadow_install_lookup(preferred, registry, alias):
    """installPreferred R/I shadow: first-match lookup over preferred ++ registry."""
    for a, v in list(preferred) + list(registry):
        if a == alias:
            return v
    return None


def shadow_release(states):
    """releaseAll R/I shadow: every present connection ends closed (False)."""
    return {a: (False if st is not None else None) for a, st in states}


# ---------- ORACLE: patch.diff behaviour via the real callees --------------

def _make_handler(aliases):
    from django.utils.connection import BaseConnectionHandler
    h = BaseConnectionHandler(settings={a: {} for a in aliases})
    h.__dict__['settings'] = {a: {} for a in aliases}
    h._connections = types.SimpleNamespace()
    return h


def oracle_install_lookup(preferred, registry):
    """Real __setitem__/__getitem__: install registry then override, then read
    back every alias. Returns {alias: value}."""
    from django.utils.connection import BaseConnectionHandler
    aliases = [a for a, _ in registry] + [a for a, _ in preferred]
    h = _make_handler(aliases)
    for a, v in registry:
        BaseConnectionHandler.__setitem__(h, a, v)
    for a, v in preferred:
        BaseConnectionHandler.__setitem__(h, a, v)
    return {a: BaseConnectionHandler.__getitem__(h, a) for a in set(aliases)}


class _FakeConn:
    def __init__(self, is_open):
        self.is_open = is_open
    def close(self):
        self.is_open = False


def oracle_release(states):
    """Real ConnectionHandler.close_all: returns {alias: post-state-bool or None}."""
    from django.db.utils import ConnectionHandler
    aliases = [a for a, _ in states]
    h = _make_handler(aliases)
    conns = {}
    for a, st in states:
        if st is None:
            continue
        c = _FakeConn(st)
        conns[a] = c
        setattr(h._connections, a, c)
    ConnectionHandler.close_all(h)
    out = {}
    for a, st in states:
        out[a] = None if st is None else conns[a].is_open
    return out


# ---------- fuzz + driver --------------------------------------------------

def fuzz_install(n, rng, pool):
    # Registry and override are dicts: unique aliases per side (mapping.md §2).
    yield ([], [])
    yield ([("default", 99)], [("default", 1)])
    yield ([("default", 99)], [("replica", 2)])
    yield ([("default", 99), ("replica", 88)], [("default", 1), ("other", 3)])
    for _ in range(n):
        rkeys = rng.sample(pool, rng.randint(0, 6))
        pkeys = rng.sample(pool, rng.randint(0, 6))
        reg = [(k, rng.randint(0, 10_000)) for k in rkeys]
        pre = [(k, rng.randint(0, 10_000)) for k in pkeys]
        yield (pre, reg)


def fuzz_release(n, rng, pool):
    yield []
    yield [("default", True)]
    yield [("default", True), ("replica", False), ("other", None)]
    for _ in range(n):
        used = rng.sample(pool, rng.randint(0, len(pool)))
        states = []
        for a in used:
            r = rng.random()
            states.append((a, None if r < 0.15 else (r < 0.55)))
        yield states


def main():
    rng = random.Random(SEED)
    pool = ["default", "replica", "other", "analytics", "legacy",
            "shard0", "shard1", "cache_db", "ro", "rw"]
    disagreements = []
    count = 0

    half = N_FUZZ // 2
    for pre, reg in fuzz_install(half, rng, pool):
        count += 1
        oracle = oracle_install_lookup(pre, reg)
        shadow = {a: shadow_install_lookup(pre, reg, a) for a in oracle}
        if shadow != oracle:
            disagreements.append(("install", (pre, reg), shadow, oracle))
            if len(disagreements) >= 5:
                break

    if not disagreements:
        for states in fuzz_release(half, rng, pool):
            count += 1
            oracle = oracle_release(states)
            shadow = shadow_release(states)
            if shadow != oracle:
                disagreements.append(("release", states, shadow, oracle))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for tag, inp, sh, orc in disagreements:
            print("  [%s] input=%r shadow=%r oracle=%r" % (tag, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of installPreferred + releaseAll agrees with "
          "patch.diff behaviour (real ConnectionHandler callees) on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
