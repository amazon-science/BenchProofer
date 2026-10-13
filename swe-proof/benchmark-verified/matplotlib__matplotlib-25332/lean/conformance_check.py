#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-25332.

The bundle models TWO transforms on the partition table of a reference-backed
grouping container (`Grouper`, lib/matplotlib/cbook.py):

    serialize    : List (Ref x List Ref) -> Except String (List (Int x List Int))
    deserialize  : List (Int x List Int) -> List (Ref x List Ref)

Post-patch rule (mapping.md / refinement.md):
    __getstate__ : succeeds, returns {"_mapping": {k(): [v() for v in vs] ...}}
    __setstate__ : self._mapping = {weakref.ref(k): [*map(weakref.ref, vs)] ...}

The ORACLE below drives the EXACT patched expressions against REAL `weakref.ref`
objects: it builds a `_mapping : dict[weakref.ref, list[weakref.ref]]` from live
holder objects (so the weak references dereference), runs the patched
`__getstate__` comprehension to serialize, and the patched `__setstate__`
comprehension to deserialize. The SHADOW is the op-for-op transliteration of
`implementation_serialize` / `implementation_deserialize` (deref via `.val` /
rewrap via `Ref.mk`, per refinement.md).

References are modeled by identity tokens (`Int`). Each token is realized as a
distinct live holder object whose `id()`-role is the token; `weakref.ref` on it
dereferences back to the token. The partition table's key ORDER is irrelevant
(a dict / Lean assoc list read by membership), so we compare serialized states
as a map  token -> multiset-of-member-tokens, and we additionally check the
ROUND-TRIP: deserialize(serialize(m)) reproduces the same partition (as a map).

stdlib-only. Pinned seed: 25332 (also in mapping.md).
"""
import random
import sys
import weakref

SEED = 25332
N = 120_000


class Holder:
    """A live, weak-referenceable object standing in for a grouped object.
    Its identity token is carried explicitly so deref is observable."""
    __slots__ = ("tok", "__weakref__")

    def __init__(self, tok):
        self.tok = tok


def _build_mapping(table):
    """table : list[(token, [member_token, ...])] -> a real
    dict[weakref.ref, list[weakref.ref]] plus the holders keeping refs alive."""
    holders = {}

    def holder(tok):
        h = holders.get(tok)
        if h is None:
            h = Holder(tok)
            holders[tok] = h
        return h

    mapping = {}
    for key_tok, member_toks in table:
        k = weakref.ref(holder(key_tok))
        vs = [weakref.ref(holder(m)) for m in member_toks]
        mapping[k] = vs
    return mapping, holders


# --- ORACLE: the EXACT patched __getstate__ / __setstate__ comprehensions -----
def oracle_getstate(mapping):
    # Convert weak refs to strong ones (patched __getstate__).
    state_mapping = {k(): [v() for v in vs] for k, vs in mapping.items()}
    # k()/v() return Holder objects; their identity token is .tok
    return {h.tok: [m.tok for m in members]
            for h, members in state_mapping.items()}


def oracle_setstate(state_tokens):
    # Rebuild holders for the strong state, then run the patched __setstate__
    # comprehension over real weakref.ref, and read back as tokens.
    holders = {}

    def holder(tok):
        h = holders.get(tok)
        if h is None:
            h = Holder(tok)
            holders[tok] = h
        return h

    strong = {holder(k): [holder(v) for v in vs] for k, vs in state_tokens}
    new_mapping = {weakref.ref(k): [*map(weakref.ref, vs)]
                   for k, vs in strong.items()}
    return [(k().tok, [v().tok for v in vs]) for k, vs in new_mapping.items()]


# --- SHADOW of the Lean implementations (R/I legs) ---------------------------
# implementation_serialize: acc=[]; for kv: deref key + each member; ok acc.
def shadow_serialize(table):
    acc = []
    for key_tok, member_toks in table:
        deref_members = []
        for v in member_toks:
            deref_members.append(v)        # Ref.val
        acc.append((key_tok, deref_members))  # key.val
    return ("ok", acc)


# implementation_deserialize: acc=[]; for kv: wrap members + key; return acc.
def shadow_deserialize(state_tokens):
    acc = []
    for key_tok, member_toks in state_tokens:
        wrap_members = []
        for v in member_toks:
            wrap_members.append(v)         # Ref.mk v  (token preserved)
        acc.append((key_tok, wrap_members))   # Ref.mk key
    return acc


def _as_map(pairs):
    """Normalize a list[(k, [members])] to {k: sorted(members)} for order-free
    comparison (keys are unique in a partition table)."""
    return {k: sorted(ms) for k, ms in pairs}


def check(table):
    mapping, _holders = _build_mapping(table)
    o_state = oracle_getstate(mapping)              # dict token -> [member tokens]
    tag, s_state = shadow_serialize(table)
    if tag != "ok":
        return ("serialize-not-ok", table, tag)
    o_state_map = {k: sorted(v) for k, v in o_state.items()}
    s_state_map = _as_map(s_state)
    if o_state_map != s_state_map:
        return ("serialize-mismatch", table, o_state_map, s_state_map)

    # round-trip: deserialize(serialize) reproduces the partition (as a map).
    state_pairs = list(s_state)
    o_round = _as_map(oracle_setstate(state_pairs))
    s_round = _as_map(shadow_deserialize(state_pairs))
    if o_round != s_round:
        return ("deserialize-mismatch", table, o_round, s_round)
    # and the round-trip must be the identity on the original partition.
    if s_round != _as_map(table):
        return ("roundtrip-not-identity", table, s_round, _as_map(table))
    return None


def _edge_cases():
    return [
        [],                                   # empty container
        [(1, [1])],                           # singleton group
        [(1, [1, 2]), (2, [1, 2])],           # one 2-element set, shared members
        [(1, [1]), (2, [2]), (3, [3])],       # three singletons
        [(5, [5, 6, 7]), (6, [5, 6, 7]), (7, [5, 6, 7])],  # one 3-set
        [(1, [])],                            # key with empty member list
        [(0, [0]), (-1, [-1])],               # zero / negative tokens
    ]


def main() -> int:
    checked = 0
    for table in _edge_cases():
        d = check(table)
        if d:
            print(f"DISAGREE edge: {d}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        ntok = rng.randint(1, 8)
        toks = rng.sample(range(1, 40), ntok)
        nkeys = rng.randint(0, ntok)
        keys = rng.sample(toks, nkeys)
        table = []
        for k in keys:
            ksize = rng.randint(0, ntok)
            members = rng.sample(toks, ksize)
            table.append((k, members))
        d = check(table)
        if d:
            print(f"DISAGREE fuzz: {d}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
