#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-1921 (plan §4.1).

Refutes (does not prove) the refinement.md legs by executing both sides on the
same fuzzed inputs and comparing observable outputs:

  * SHADOW — the impl region of Solution.lean transliterated to Python over the
             *real* repo carrier (a dict / mapping of per-key settings), via the
             mapping.md bijection (`List Int` position ↔ dict key; `absent`(=0)
             ↔ key absent; `noneVal`(=-1) ↔ the value `None`; any other int ↔ an
             ordinary value). This is the deep model `combinedSeq` /
             `combined` / `effective` spelled out in Solution.lean's `pure`
             region and discharged by the verified loop.
  * ORACLE — patch.diff's behaviour: the real repository combine-and-drop
             operation with the gold patch applied (the real correctness oracle,
             G-RESOLVE). We drive the REAL repository machinery (the per-request
             precedence merge plus the final drop the gold patch adds), so the
             A-reference (`combined` == the real operation) is exercised against
             live code rather than trusted.

They must agree on the per-key value mapping of the result for every input. Exit
0 iff zero disagreements; any disagreement is a mechanical fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + the package
under evaluation. The fuzz seed is pinned for a deterministic verdict.
"""
import random
import sys
from collections import OrderedDict

SEED = 1921
N_FUZZ = 100_000

# Sentinels of the model carrier (mapping.md §2).
ABSENT = 0      # key not carried by this collection
NONE_VAL = -1   # the explicit unset value a caller may store under a key


# --- the deep-model SHADOW: Solution.lean effective / combined --------------
def effective(sv, rv):
    # per-request value wins where the per-request collection carries the key
    return rv if rv != ABSENT else sv


def combined(sv, rv):
    ev = effective(sv, rv)
    return ABSENT if ev == NONE_VAL else ev


def shadow_merge(session_vals, request_vals):
    """combinedSeq over the shared key universe 0..n-1, returned as the per-key
    value mapping {key: real_value} of the result, dropping ABSENT positions
    (which model 'key not present in the returned collection')."""
    n = min(len(session_vals), len(request_vals))
    out = {}
    for k in range(n):
        v = combined(session_vals[k], request_vals[k])
        if v != ABSENT:
            out[k] = v
    return out


# --- the repository ORACLE: the gold combine-and-drop -----------------------
def _to_dicts(session_vals, request_vals):
    """Lift the integer carrier back to the real repository types: each position
    becomes a string key; ABSENT means the key is omitted from that side;
    NONE_VAL becomes the Python value None; any other int stays as itself."""
    n = min(len(session_vals), len(request_vals))
    session, request = OrderedDict(), OrderedDict()
    for k in range(n):
        sv, rv = session_vals[k], request_vals[k]
        if sv != ABSENT:
            session[str(k)] = None if sv == NONE_VAL else sv
        if rv != ABSENT:
            request[str(k)] = None if rv == NONE_VAL else rv
    return session, request


def oracle_merge(session_vals, request_vals):
    """patch.diff's behaviour: drive the REAL repository merge-and-drop (the
    per-request precedence merge plus the gold final drop of every key whose
    merged value is None). Returns the per-key value mapping of the result keyed
    by the same integer key universe as the shadow."""
    from requests.sessions import merge_setting
    session, request = _to_dicts(session_vals, request_vals)
    # merge_setting(request_setting, session_setting): the per-request side wins.
    merged = merge_setting(request, session, dict_class=OrderedDict)
    # The gold patch guarantees no surviving key maps to None; assert it and key
    # the result by the integer key universe for comparison with the shadow.
    out = {}
    for sk, v in merged.items():
        assert v is not None, "oracle returned a None-valued key (drop missing)"
        out[int(sk)] = v
    return out


def fuzz_inputs(n, rng):
    # value alphabet: absent, the unset value, and a few ordinary values
    alphabet = [ABSENT, NONE_VAL, 1, 2, 7]
    # boundary cases first (plan §4.1 step 4)
    yield ([], [])
    yield ([NONE_VAL], [ABSENT])      # session-only unset key -> must drop
    yield ([ABSENT], [NONE_VAL])      # request-only unset key -> must drop
    yield ([NONE_VAL], [NONE_VAL])    # both unset -> drop
    yield ([5], [NONE_VAL])           # request unsets a real session value -> drop
    yield ([NONE_VAL], [5])           # request overrides an unset session value
    yield ([5], [ABSENT])             # session-only real value survives
    yield ([ABSENT], [5])             # request-only real value survives
    yield ([5], [7])                  # both supply distinct real values -> request wins
    yield ([1, NONE_VAL, 3], [ABSENT, ABSENT, ABSENT])
    for _ in range(n):
        k = rng.randint(0, 8)
        s = [rng.choice(alphabet) for _ in range(k)]
        r = [rng.choice(alphabet) for _ in range(k)]
        yield (s, r)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for sv, rv in fuzz_inputs(N_FUZZ, rng):
        count += 1
        try:
            shadow = shadow_merge(sv, rv)
            oracle = oracle_merge(sv, rv)
        except Exception as e:  # noqa: BLE001
            disagreements.append((sv, rv, "shadow/oracle", repr(e)))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != oracle:
            disagreements.append((sv, rv, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for sv, rv, sh, orc in disagreements:
            print("  session=%r request=%r shadow=%r oracle=%r" % (sv, rv, sh, orc))
        return 1
    print("G-CONF OK: deep-model shadow of effectiveCollection agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
