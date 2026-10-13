#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_loadPipeline
against the POST-PATCH behaviour of BaseHandler.load_middleware's chain-assembly
loop (django/core/handlers/base.py:39-89 @ base_commit + patch.diff).

The impl region is NOT all-A-tagged: the changed control/data-flow of the loop
(which mode each stage is wired under, and the frame a declined stage leaves on
the running handler) is modeled DEEPLY by `wireStage`/`assemble`/`stageMode`
(the R/I content). The single A-reference `adaptedMode` (the UNCHANGED
`adapt_method_mode`'s effect on the handler's actual mode) is left as the REAL
adapter logic in the oracle leg — G-AX owns its soundness.

Bridge (mapping.md §2): the running handler is a pair
(handler_is_async, iscoroutinefunction(handler)) == (Chain.flag, Chain.hmode);
each processed middleware `reversed(MIDDLEWARE)[i]` == `stages[i]` via its
(sync_capable, async_capable, installs?) booleans; the base
`convert_exception_to_response(get_response)` starts consistent at `is_async`
(== init.flag == init.hmode). The observable diffed is the final assembled
chain's (recorded, actual) mode pair — the chain-consistency the patch restores.

Oracle: the POST-PATCH loop, reproduced VERBATIM in its mode-tracking form from
the patched source, over the finite (is_async) x (list of stages) fuzzing space.
The un-patched (pre-patch) loop is also reproduced to confirm the fuzzer
actually exercises the discriminating skip path (sanity, not part of the pass
condition). stdlib-only. exit 0 iff zero disagreements shadow-vs-postpatch.
"""
import json
import random
import sys

SEED = 13810          # pinned in mapping.md §4
N = 150_000           # >= 10^5


# ---------------------------------------------------------------------------
# A-reference (validated by G-AX, left REAL here): the actual execution mode of
# adapt_method_mode(is_async=target, method, method_is_async=flag)'s return
# value, given the running handler's current actual mode `actual`.
#   if target and not flag:      sync_to_async wrap -> True
#   elif not target and flag:    async_to_sync wrap -> False
#   else:                        method returned unchanged -> actual
# ---------------------------------------------------------------------------
def adapt_actual_mode(target, flag, actual):
    if target and not flag:
        return True
    if not target and flag:
        return False
    return actual


# The mode-selection ladder (base.py:43-51). Stages advertising neither
# capability raise RuntimeError and never reach the loop body (excluded, §2).
def selection_mode(handler_is_async, can_sync, can_async):
    if not handler_is_async and can_sync:
        return False
    return can_async


# ---------------------------------------------------------------------------
# Oracle: the POST-PATCH load_middleware assembly loop, in mode-tracking form.
# `handler_is_async` == recorded mode; `handler_actual` == iscoroutinefunction
# of the running handler. A stage is (can_sync, can_async, installs).
# The gold fix: the adapter output is committed to the running handler ONLY in
# the no-exception `else:` branch (installs); a declined stage `continue`s,
# leaving BOTH the recorded mode and the running handler untouched.
# ---------------------------------------------------------------------------
def oracle_postpatch(is_async, stages):
    handler_is_async = is_async
    handler_actual = is_async     # base handler built consistently at is_async
    for can_sync, can_async, installs in stages:
        middleware_is_async = selection_mode(handler_is_async, can_sync, can_async)
        adapted_actual = adapt_actual_mode(
            middleware_is_async, handler_is_async, handler_actual)
        if not installs:
            # MiddlewareNotUsed -> continue: running handler untouched.
            continue
        else:
            handler_actual = adapted_actual
            handler_is_async = middleware_is_async
    return (handler_is_async, handler_actual)


# The PRE-PATCH loop (only used to confirm the fuzzer exercises the skip path;
# NOT part of the pass condition). Here the adapter output poisons the running
# handler's actual mode before the try knows the outcome, and on the skip path
# the recorded mode is left behind -> desync.
def oracle_prepatch(is_async, stages):
    handler_is_async = is_async
    handler_actual = is_async
    for can_sync, can_async, installs in stages:
        middleware_is_async = selection_mode(handler_is_async, can_sync, can_async)
        handler_actual = adapt_actual_mode(
            middleware_is_async, handler_is_async, handler_actual)
        if not installs:
            continue
        handler_is_async = middleware_is_async
    return (handler_is_async, handler_actual)


# ---------------------------------------------------------------------------
# Shadow: the R/I reconstruction of implementation_loadPipeline
#   stageMode / wireStage / assemble transliterated; adaptedMode == the same
#   A-reference `adapt_actual_mode` (mapping: adaptedMode hmode flag target).
# ---------------------------------------------------------------------------
def shadow_stage_mode(flag, can_sync, can_async):
    if (flag is False) and (can_sync is True):
        return False
    return can_async


def shadow_adapted_mode(hmode, flag, target):
    return hmode if flag == target else target


def shadow_wire(chain, stage):
    flag, hmode = chain
    can_sync, can_async, usable = stage
    target = shadow_stage_mode(flag, can_sync, can_async)
    amode = shadow_adapted_mode(hmode, flag, target)
    if usable:
        return (target, amode)
    return chain


def shadow_assemble(is_async, stages):
    chain = (is_async, is_async)     # init consistent at is_async
    for stage in stages:
        chain = shadow_wire(chain, stage)
    return chain


# ---------------------------------------------------------------------------
def gen_stages(rng):
    n = rng.randint(0, 8)
    out = []
    for _ in range(n):
        # exclude the neither-capable stage (RuntimeError; never reaches loop)
        while True:
            cs = rng.random() < 0.6
            ca = rng.random() < 0.5
            if cs or ca:
                break
        installs = rng.random() < 0.5     # ~half decline (skip path)
        out.append((cs, ca, installs))
    return out


def main():
    rng = random.Random(SEED)

    # a few hand-picked discriminating cases: async base + a declining
    # async-incapable stage followed by more stages (the poisoning scenario)
    fixed = [
        (True,  [(True, False, False), (True, True, True)]),
        (True,  [(True, False, False)]),
        (False, [(True, False, False), (True, True, True)]),
        (True,  []),
        (True,  [(True, True, True), (True, False, False), (False, True, True)]),
        (True,  [(True, False, True), (True, False, False)]),
    ]

    cases = list(fixed)
    for _ in range(N):
        cases.append((rng.random() < 0.5, gen_stages(rng)))

    disagreements = []
    skip_path_exercised = False
    for is_async, stages in cases:
        want = oracle_postpatch(is_async, stages)
        got = shadow_assemble(is_async, stages)
        if got != want:
            if len(disagreements) < 12:
                disagreements.append((is_async, stages, got, want))
        if oracle_prepatch(is_async, stages) != oracle_postpatch(is_async, stages):
            skip_path_exercised = True

    if disagreements:
        print(f"G-CONF FAIL: {len(disagreements)}+ disagreements / {len(cases)} inputs")
        for is_async, stages, g, w in disagreements:
            print(f"  is_async={is_async} stages={stages} shadow={g} postpatch={w}")
        return 1

    print(json.dumps({
        "gate": "G-CONF",
        "status": "pass",
        "inputs": len(cases),
        "disagreements": 0,
        "seed": SEED,
        "skip_path_exercised": skip_path_exercised,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
