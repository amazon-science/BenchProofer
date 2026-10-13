#!/usr/bin/env python
"""G-CONF for psf__requests-1921.

Differential test of the R/I legs of `implementation_effectiveSetting` against
the PATCHED repo function (the gate git-applies the gold patch before running
this, so `requests.sessions.merge_setting` here is the fixed code).

Modeled (R/I) behavior: given a per-request mapping and a session-default
mapping (both dictionaries), the effective mapping is the session defaults
overlaid by the request entries (request wins by key), with the null sentinel
(`None`) honored so that NO null-valued entry survives — whether the null came
from the request mapping or from the session defaults.

Shadow (this file): replicate that logic in Python directly from the
`List Entry` model (ordered assoc-list, unique keys). Oracle: the real patched
`merge_setting(request_setting, session_setting)`. We exercise the both-dicts
tail (the only branch the fix touches), so both inputs are always dicts.

The model uses the DEFAULT `dict_class=OrderedDict` (case-sensitive keys); the
header call site's `CaseInsensitiveDict` is an orthogonal key-type concern the
fix does not touch, so we fuzz case-disjoint keys under OrderedDict.

stdlib + requests only. Exit 0 iff zero disagreements over >=1e5 fuzzed inputs.
"""
import random
import sys
from collections import OrderedDict

from requests.sessions import merge_setting

SEED = 1921
N = 100_000

KEY_POOL = ["Accept-Encoding", "User-Agent", "Authorization", "X-Custom",
            "Connection", "Accept", "Cookie", "Host", "k1", "k2"]
VAL_POOL = ["gzip", "v1", "v2", "", "token abc", "0", "None", "keep-alive"]


def shadow(req_items, ses_items):
    """The R/I shadow of implementation_effectiveSetting, on assoc-list models.
    req_items / ses_items are lists of (key, value-or-None), unique keys."""
    # 1 (R): start from session defaults.
    merged = list(ses_items)
    # 2 (R): overlay request entries by key (request wins; replace in place).
    for k, v in req_items:
        for i, (mk, _) in enumerate(merged):
            if mk == k:
                merged[i] = (k, v)
                break
        else:
            merged.append((k, v))
    # 3 (I): drop keys the request maps to None.
    for k, v in req_items:
        if v is None:
            merged = [(mk, mv) for (mk, mv) in merged if mk != k]
    # 4 (I): drop every remaining None-valued entry (the fix).
    merged = [(mk, mv) for (mk, mv) in merged if mv is not None]
    return merged


def gen_mapping(rng):
    n = rng.randint(0, 5)
    keys = rng.sample(KEY_POOL, n)
    items = []
    for k in keys:
        # ~35% chance the value is the null sentinel.
        v = None if rng.random() < 0.35 else rng.choice(VAL_POOL)
        items.append((k, v))
    return items


def main():
    rng = random.Random(SEED)
    checked = 0
    for i in range(N):
        req_items = gen_mapping(rng)
        ses_items = gen_mapping(rng)
        req = OrderedDict(req_items)
        ses = OrderedDict(ses_items)
        want = list(merge_setting(req, ses).items())
        got = shadow(req_items, ses_items)
        if got != want:
            print(f"DISAGREEMENT at case {i}: req={req_items} ses={ses_items}\n"
                  f"  oracle={want}\n  shadow={got}")
            print("G-CONF FAIL")
            sys.exit(1)
        checked += 1
    print(f"G-CONF OK: {checked} cases agree (of {N}), seed={SEED}")
    sys.exit(0)


if __name__ == "__main__":
    main()
