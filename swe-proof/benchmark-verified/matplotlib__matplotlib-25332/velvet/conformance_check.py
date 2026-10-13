#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-25332 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's two impl regions transliterated
              to Python over the carrier `List (Ref × List Ref)`, via the mapping.md
              bijection (a `weakref.ref`/strong object ↔ `Ref{target=id(referent),
              weak=…}`; an ordered dict ↔ the list of its items):
                snapshot ↔ strongifyMap (every reference made strong: weak=False)
                rebuild  ↔ weakenMap    (every reference made weak:   weak=True)
              Both folds keep each reference's `target` (the object it points at).
              There are NO A-tagged callees in either impl region — the per-
              reference flip IS the modeled change — so the shadow is pure R/I.
  * ORACLE  — patch.diff's behaviour: the REAL patched
              `matplotlib.cbook.Grouper.__getstate__` (for snapshot) and
              `Grouper.__setstate__` (for rebuild), run on randomly-built
              reference tables. The harness git-applies patch.diff before this
              runs (apply_gold=True), so these methods exist and are the gold ones.

They must agree on every input — compared as the per-row tuple
(key-target-identity, weak-flag) and (member-target-identities, weak-flags).
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the patched SWE-Bench instance image), stdlib + matplotlib
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
import weakref

from matplotlib.cbook import Grouper

SEED = 25332
N_FUZZ = 100_000


class O:
    """A minimal weak-referenceable, hashable object standing for one referent
    in the grouping registry (an Axes, in the real figure)."""
    __slots__ = ("__weakref__", "name")

    def __init__(self, name):
        self.name = name


# --- the R/I shadow: Solution.lean strongify/weaken, transliterated ----------
# A `Ref` is modeled as the pair (target, weak); a table row as (Ref, [Ref]); a
# table as a list of rows. `target` is object identity (id), `weak` the flag.

def strongify(ref):          # weak := false, target kept
    target, _weak = ref
    return (target, False)


def weaken(ref):             # weak := true, target kept
    target, _weak = ref
    return (target, True)


def strongify_map(table):    # strongifyMap: per-row, key + every member
    return [(strongify(k), [strongify(v) for v in vs]) for (k, vs) in table]


def weaken_map(table):       # weakenMap
    return [(weaken(k), [weaken(v) for v in vs]) for (k, vs) in table]


# --- bridging: live repr <-> carrier (mapping.md §2 bijection) ----------------

def carrier_from_weak_mapping(mapping):
    """A live `Grouper._mapping` (weakref keys -> list of weakrefs) as the
    carrier of weak `Ref`s (weak=True)."""
    out = []
    for wk, vs in mapping.items():
        key = (id(wk()), True)
        members = [(id(v()), True) for v in vs]
        out.append((key, members))
    return out


def carrier_from_strong_mapping(mapping):
    """A snapshot `_mapping` (strong-object keys -> list of strong objects) as
    the carrier of strong `Ref`s (weak=False)."""
    out = []
    for k, vs in mapping.items():
        key = (id(k), False)
        members = [(id(v), False) for v in vs]
        out.append((key, members))
    return out


def oracle_getstate_carrier(state_mapping):
    """The patched __getstate__'s `_mapping`: strong-object keys -> strong
    objects. Carried as strong `Ref`s (weak=False)."""
    return carrier_from_strong_mapping(state_mapping)


def oracle_setstate_carrier(result_mapping):
    """The patched __setstate__'s rebuilt `_mapping`: weakref keys -> weakrefs.
    Carried as weak `Ref`s (weak=True)."""
    return carrier_from_weak_mapping(result_mapping)


# --- fuzzing ------------------------------------------------------------------

def build_random_table(rng, keepalive):
    """Build a random live `_mapping`: weakref keys -> lists of weakrefs, over
    fresh objects (kept alive via `keepalive`). Returns the dict."""
    n_rows = rng.randint(0, 8)
    mapping = {}
    for _ in range(n_rows):
        k = O("k%d" % len(keepalive))
        keepalive.append(k)
        n_members = rng.randint(1, 5)
        members = []
        for _ in range(n_members):
            # a member may be the key itself (singleton-style) or a fresh object
            if members and rng.random() < 0.3:
                m = rng.choice(members + [k])
            else:
                m = O("m%d" % len(keepalive))
                keepalive.append(m)
            members.append(m)
        mapping[weakref.ref(k)] = [weakref.ref(m) for m in members]
    return mapping


def check_snapshot(rng, keepalive):
    """snapshot ↔ Grouper.__getstate__: strongify every reference."""
    live = build_random_table(rng, keepalive)
    g = Grouper()
    g._mapping = live
    state = g.__getstate__()                       # REAL patched callee
    oracle = oracle_getstate_carrier(state["_mapping"])
    shadow = strongify_map(carrier_from_weak_mapping(live))
    assert oracle == shadow, (
        "snapshot R/I disagreement:\n  oracle=%r\n  shadow=%r" % (oracle, shadow))


def check_rebuild(rng, keepalive):
    """rebuild ↔ Grouper.__setstate__: weaken every reference."""
    # Build a strong-form state (as __getstate__ would have produced): strong
    # object keys -> lists of strong objects.
    n_rows = rng.randint(0, 8)
    strong_mapping = {}
    for _ in range(n_rows):
        k = O("sk%d" % len(keepalive))
        keepalive.append(k)
        n_members = rng.randint(1, 5)
        members = []
        for _ in range(n_members):
            if members and rng.random() < 0.3:
                m = rng.choice(members + [k])
            else:
                m = O("sm%d" % len(keepalive))
                keepalive.append(m)
            members.append(m)
        strong_mapping[k] = members
    g = Grouper()
    g.__setstate__({"_mapping": dict(strong_mapping)})   # REAL patched callee
    oracle = oracle_setstate_carrier(g._mapping)
    shadow = weaken_map(carrier_from_strong_mapping(strong_mapping))
    assert oracle == shadow, (
        "rebuild R/I disagreement:\n  oracle=%r\n  shadow=%r" % (oracle, shadow))


def main():
    rng = random.Random(SEED)
    count = 0
    keepalive = []           # keep all referents alive for the duration
    try:
        for _ in range(N_FUZZ // 2):
            check_snapshot(rng, keepalive)
            check_rebuild(rng, keepalive)
            count += 2
            # bound memory: periodically drop the keepalive (the tables built so
            # far have already been compared and are no longer needed)
            if len(keepalive) > 50_000:
                keepalive = []
    except AssertionError as e:
        print("G-CONF FAIL after %d inputs (seed=%d):\n%s" % (count, SEED, e))
        return 1
    print("G-CONF OK: R/I shadow of snapshot/rebuild agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
