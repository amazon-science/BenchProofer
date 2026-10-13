#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-25332
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant) stripped. The model IS Python over plain
List[int], so no shim is needed. There are no @Pure helpers and no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo methods the model models per mapping.md —
`matplotlib.cbook.Grouper.__getstate__` (capture_state) and
`Grouper.__setstate__` (restore_state); their composition is
roundtrip_weakness. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md sections 1-2): the container's `_mapping` dict (keys
plus per-key value-lists, all handles) flattens in iteration order to two
parallel lists — ident[i] = the integer identity (id) of the referent the
i-th handle resolves to, weak[i] = 1 iff the slot holds an indirect handle
(a weakref.ref), 0 iff it holds the target directly (a strong reference).
Both real methods are dict/list comprehensions, so iteration order is
preserved slot for slot and the flattening is order-stable across the
transform.

Diff protocol, per handle set:
  capture: flatten the live container -> (ident, weak); shadow
    capture_state(ident, weak) vs the flattening of the real
    __getstate__()["_mapping"] — directness flags must agree slot for slot,
    and the captured identity list must equal `ident` (the shadow leaves
    `ident` untouched; the real capture must preserve each slot's resolved
    identity).
  restore: shadow restore_state(ident, captured_flags) vs the flattening of
    a fresh container after real __setstate__ on the captured state — same
    two obligations (the captured flags are all 0, satisfying the shadow's
    Requires, because the capture check above already ran).
  round trip: shadow roundtrip_weakness(ident, weak) vs the restored
    container's flags/identities from the real getstate-then-setstate
    composition.

Input domain: Requires demands only len(weak) == len(ident), which the
flattening satisfies by construction; every generated handle set is
Requires-satisfying. Generation covers the empty container, singletons,
merged groups (join), duplicates, and randomized fuzz over sizes 0..8 with
random group merges.

>= 1e5 Requires-satisfying inputs: 8 boundary handle sets + 100000 fuzz sets.
Pinned fuzz seed: 25332.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
import weakref

SEED = 25332
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def capture_state(ident, weak):
    out = []  # type: list
    i = 0
    while i < len(ident):
        # Resolving the indirect handle to its target's identity (ident[i]) and
        # storing it as a direct handle: the captured slot is direct (flag 0).
        out.append(0)
        i = i + 1
    return out


def restore_state(ident, state_weak):
    out = []  # type: list
    i = 0
    while i < len(ident):
        # Constructing an indirect handle around the target identity ident[i]:
        # the rebuilt slot is indirect (flag 1).
        out.append(1)
        i = i + 1
    return out


def roundtrip_weakness(ident, weak):
    captured = capture_state(ident, weak)
    restored = restore_state(ident, captured)
    return restored


# --- bridge: container mapping <-> parallel (ident, weak) lists --------------

class _Member:
    """A weak-referenceable container member (stands for an Artist)."""
    __slots__ = ("tag", "__weakref__")

    def __init__(self, tag):
        self.tag = tag


def flatten(mapping):
    """Flatten a handle mapping (keys + value-lists, iteration order) to the
    model's parallel lists: ident[i] = id of the slot's referent, weak[i] = 1
    iff the slot holds an indirect handle (weakref.ref), else 0."""
    ident, weak = [], []
    for k, vs in mapping.items():
        for h in (k, *vs):
            if isinstance(h, weakref.ReferenceType):
                ident.append(id(h()))
                weak.append(1)
            else:
                ident.append(id(h))
                weak.append(0)
    return ident, weak


def check_set(Grouper, objs, joins):
    """Build a container over objs (applying the given join pairs), then diff
    shadow vs real on capture, restore, and the round trip. Returns an error
    string on the first disagreement, else None."""
    live = Grouper(objs)
    for a, b in joins:
        live.join(objs[a], objs[b])

    ident, weak = flatten(live._mapping)

    def fail(stage, shadow_out, real_flags, real_ident):
        return ("DISAGREEMENT (%s)\n  objs=%r joins=%r\n  ident=%r weak=%r\n"
                "  shadow_flags=%r\n  real_flags=%r\n  real_ident=%r"
                % (stage, [o.tag for o in objs], joins, ident, weak,
                   shadow_out, real_flags, real_ident))

    # capture: shadow flags vs the real captured state's flags; identity
    # preservation = the captured identity list equals the live one.
    state = live.__getstate__()
    cap_ident, cap_flags = flatten(state["_mapping"])
    shadow_cap = capture_state(ident, weak)
    if shadow_cap != cap_flags or cap_ident != ident:
        return fail("capture", shadow_cap, cap_flags, cap_ident)

    # restore: real __setstate__ on the captured state (all-direct, so the
    # shadow's Requires on state_weak holds), on a fresh instance as the
    # serialisation machinery would drive it.
    fresh = Grouper.__new__(Grouper)
    fresh.__setstate__(state)
    res_ident, res_flags = flatten(fresh._mapping)
    shadow_res = restore_state(ident, cap_flags)
    if shadow_res != res_flags or res_ident != ident:
        return fail("restore", shadow_res, res_flags, res_ident)

    # round trip: the composition, against the same restored container.
    shadow_rt = roundtrip_weakness(ident, weak)
    if shadow_rt != res_flags:
        return fail("roundtrip", shadow_rt, res_flags, res_ident)

    return None


def boundary_sets():
    """(n_objs, joins) shapes: empty, singleton, disjoint slots, merged
    groups, chains, everything-in-one-group."""
    return [
        (0, []),
        (1, []),
        (2, []),
        (2, [(0, 1)]),
        (3, [(0, 1)]),
        (3, [(0, 1), (1, 2)]),
        (4, [(0, 1), (2, 3)]),
        (5, [(0, 1), (1, 2), (2, 3), (3, 4)]),
    ]


def main():
    from matplotlib.cbook import Grouper  # REAL patched class

    checked = 0
    for n, joins in boundary_sets():
        objs = [_Member(t) for t in range(n)]
        err = check_set(Grouper, objs, joins)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 8)
        objs = [_Member(rng.randint(-1000, 1000)) for _ in range(n)]
        joins = []
        if n >= 2:
            for _ in range(rng.randint(0, n)):
                a = rng.randrange(n)
                b = rng.randrange(n)
                if a != b:
                    joins.append((a, b))
        err = check_set(Grouper, objs, joins)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real capture/restore on %d handle sets "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_sets()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
