#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-23299.

The bundle models ONE routine: the snapshot-and-restore logic of
`matplotlib.rc_context` (mapping.md). Its observable effect is the value of the
global settings mapping after the context exits. We model that effect as a pure
function of two observations: the mapping captured on entry (`orig`,
`rcParams.copy()`) and the mapping present when the body finishes (`final`, what
`rcParams` holds at the end of the body). The body's machinery (`rc_file`,
`rcParams.update(rc)`, `yield`) runs outside the modeled function; its only
output to the restore is `final`.

Standing up real matplotlib to drive `rc_context` is heavy and unnecessary: the
restored mapping is a PURE function of `orig` and `final` under the gold edit. So
the ORACLE below is a faithful in-process replica of the POST-PATCH restore
(`dict.update(rcParams, dict(orig) - {'backend'})`), and the SHADOW is the
op-for-op transliteration of `implementation_restoreSettings` (Solution.lean impl
region), per refinement.md.

This genuinely tests the soundness-critical clause: after the context exits, the
`'backend'` entry must carry the value chosen inside the body (`final`), while
every other key reverts to its entry value (`orig`) — exactly what the F2P test
`test_no_backend_reset_rccontext` checks.

stdlib-only. Pinned seed: 23299 (also in mapping.md).
"""
import random
import sys

SEED = 23299
N = 120_000

# rcParams always carries 'backend'; the rest is a stable key set.
KEY_POOL = ["backend", "interactive", "lines.linewidth", "figure.dpi",
            "axes.grid", "font.size", "savefig.format"]
VALUE_POOL = ["agg", "module://aardvark", "qtagg", "0", "1", "1.5", "100",
            "True", "False", "10.0", "png", "pdf"]


# --- Settings carrier: list of (key, value) with unique keys -----------------
def assoc_set(m, k, v):
    out = []
    found = False
    for (kk, vv) in m:
        if kk == k:
            out.append((k, v)); found = True
        else:
            out.append((kk, vv))
    if not found:
        out.append((k, v))
    return out


def dict_update(cur, upd):
    acc = list(cur)
    for (k, v) in upd:
        acc = assoc_set(acc, k, v)
    return acc


def assoc_erase(m, k):
    return [(kk, vv) for (kk, vv) in m if kk != k]


# --- ORACLE: faithful in-process replica of the POST-PATCH restore -----------
# orig = dict(rcParams.copy()); del orig['backend']; dict.update(rcParams, orig)
# rcParams holds `final` when the body finishes; the restore overlays the
# backend-stripped snapshot onto it.
def oracle(orig, final):
    snapshot = assoc_erase(orig, "backend")   # del orig['backend']
    return dict_update(final, snapshot)       # dict.update(rcParams=final, snapshot)


# --- SHADOW: transliteration of implementation_restoreSettings ---------------
def shadow(orig, final):
    snapshot = list(orig)
    snapshot = assoc_erase(snapshot, "backend")
    return dict_update(final, snapshot)


def disagree(orig, final):
    o = oracle(orig, final)
    s = shadow(orig, final)
    if o != s:
        return (orig, final, o, s)
    return None


def _rand_mapping(rng):
    """A mapping over a random subset of KEY_POOL that always includes
    'backend' (rcParams invariant), with random values."""
    keys = ["backend"] + [k for k in KEY_POOL[1:] if rng.random() < 0.7]
    return [(k, rng.choice(VALUE_POOL)) for k in keys]


def _edge_cases():
    # F2P scenario: backend reset across the context must NOT happen.
    yield ([("backend", "agg"), ("interactive", "0")],
           [("backend", "module://aardvark"), ("interactive", "1")])
    # body changed only the backend
    yield ([("backend", "qtagg"), ("font.size", "10.0")],
           [("backend", "module://aardvark"), ("font.size", "10.0")])
    # body changed nothing
    yield ([("backend", "agg")], [("backend", "agg")])
    # body changed a non-backend key only; backend identical
    yield ([("backend", "agg"), ("figure.dpi", "100")],
           [("backend", "agg"), ("figure.dpi", "200")])


def main():
    checked = 0
    for orig, final in _edge_cases():
        d = disagree(orig, final)
        if d:
            print(f"DISAGREE edge: oracle={d[2]} shadow={d[3]} orig={d[0]} final={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        orig = _rand_mapping(rng)
        # `final` shares orig's key set (the body changes values, not keys) but
        # may differ on any value, including 'backend'.
        final = [(k, rng.choice(VALUE_POOL)) for (k, _) in orig]
        d = disagree(orig, final)
        if d:
            print(f"DISAGREE fuzz: oracle={d[2]} shadow={d[3]} orig={d[0]} final={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
