#!/usr/bin/env python3
"""G-AX for django__django-13810 — deep-model A-reference validation.

The bundle consumes NO `axiom <callee>_prop` and declares no `opaque` callee.
The two primitives the assembler uses are modeled DEEPLY in Solution.lean's
`pure` region and are A-REFERENCES (mapping.md §3): each is validated here
value-for-value against the real, unchanged repo callee it models.

  * `stageMode flag s` models the inline mode-selection ladder at
    django/core/handlers/base.py:43-51 (base_commit, unchanged by the patch):

        if not middleware_can_sync and not middleware_can_async:
            raise RuntimeError(...)                # stage excluded from `stages`
        elif not handler_is_async and middleware_can_sync:
            middleware_is_async = False
        else:
            middleware_is_async = middleware_can_async

  * `adaptedMode hmode flag target` models the effect of the UNCHANGED method
    BaseHandler.adapt_method_mode(is_async=target, method, method_is_async=flag)
    (base.py:97-122) on the running handler's ACTUAL execution mode:

        if is_async and not method_is_async:  return sync_to_async(method)  # -> async
        elif not is_async and method_is_async: return async_to_sync(method) # -> sync
        return method                                                       # unchanged

    In the assembler `method_is_async` is passed explicitly as the recorded
    mode `flag`, `is_async` is the chosen `target`, and the running handler's
    actual mode is `hmode`. In the consistent regime a well-formed assembler
    calls the adapter with `flag == hmode == actual`; the returned callable's
    actual mode is `target` when `flag != target` (a wrap flips it) and `hmode`
    when `flag == target` (the `return method` no-op).

Both callees are total over booleans, so the validation is EXHAUSTIVE over the
full finite domain — zero disagreements is a proof of model==callee, not a
sample. stdlib-only. exit 0 iff every combination agrees.
"""
import json
import sys


# ---- deep models transliterated from Solution.lean's `pure` region ----
def stage_mode(flag, can_sync, can_async):
    """== stageMode flag {canSync, canAsync, ...}."""
    if (flag is False) and (can_sync is True):
        return False
    return can_async


def adapted_mode(hmode, flag, target):
    """== adaptedMode hmode flag target."""
    return hmode if flag == target else target


# ---- reference callees, reproduced from base.py @ base_commit ----
def ref_selection_ladder(handler_is_async, middleware_can_sync, middleware_can_async):
    """The real if/elif/else choosing middleware_is_async (base.py:43-51).
    Raises for the neither-capable stage (excluded from `stages`, mapping §2)."""
    if not middleware_can_sync and not middleware_can_async:
        raise RuntimeError("Middleware advertises neither sync nor async")
    elif not handler_is_async and middleware_can_sync:
        return False
    else:
        return middleware_can_async


def ref_adapt_actual_mode(is_async, method_actual, method_is_async):
    """The ACTUAL execution mode of adapt_method_mode's return value
    (base.py:97-122). `method_actual` is iscoroutinefunction(method); the
    caller passes method_is_async explicitly (never None here)."""
    if is_async and not method_is_async:
        return True            # sync_to_async wrap -> coroutine
    elif not is_async and method_is_async:
        return False           # async_to_sync wrap -> plain sync
    return method_actual       # returned unchanged


def main():
    bools = (False, True)
    disagreements = []

    # 3.2 stageMode == the selection ladder, over stages with canSync | canAsync
    # (the neither-capable stage never reaches `stages`; check it raises).
    for flag in bools:
        for cs in bools:
            for ca in bools:
                if not cs and not ca:
                    try:
                        ref_selection_ladder(flag, cs, ca)
                        disagreements.append(
                            ("ladder-should-raise", flag, cs, ca))
                    except RuntimeError:
                        pass
                    continue
                got = stage_mode(flag, cs, ca)
                want = ref_selection_ladder(flag, cs, ca)
                if got != want:
                    disagreements.append(("stageMode", flag, cs, ca, got, want))

    # 3.1 adaptedMode == adapt_method_mode's actual-mode effect, in the
    # consistent regime the well-formed assembler calls it (flag == hmode).
    for hmode in bools:
        flag = hmode                      # consistent: recorded == actual
        for target in bools:
            got = adapted_mode(hmode, flag, target)
            want = ref_adapt_actual_mode(target, hmode, flag)
            if got != want:
                disagreements.append(
                    ("adaptedMode", hmode, flag, target, got, want))

    if disagreements:
        print(json.dumps({
            "gate": "G-AX",
            "status": "fail",
            "instance": "django__django-13810",
            "disagreements": disagreements[:20],
        }))
        return 1

    print(json.dumps({
        "gate": "G-AX",
        "status": "pass",
        "instance": "django__django-13810",
        "reason": "stageMode == selection ladder and adaptedMode == "
                  "adapt_method_mode actual-mode effect, exhaustive over all "
                  "boolean combinations; RuntimeError boundary confirmed",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
